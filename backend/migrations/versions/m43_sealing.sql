CREATE FUNCTION flare_sealing.quote_string(v text) RETURNS text
LANGUAGE plpgsql IMMUTABLE STRICT AS $$
DECLARE s text := replace(replace(v, chr(92), chr(92)||chr(92)), '"', chr(92)||'"');
BEGIN
    FOR n IN 1..31 LOOP
        s := replace(s, chr(n), chr(92)||'u'||lpad(to_hex(n),4,'0'));
    END LOOP;
    RETURN '"'||s||'"';
END $$;
-- next function
CREATE FUNCTION flare_sealing.json_value(v jsonb, tagged boolean) RETURNS text
LANGUAGE plpgsql IMMUTABLE STRICT SET search_path = pg_catalog, flare_sealing AS $$
DECLARE k text := jsonb_typeof(v); body text;
BEGIN
    CASE k
    WHEN 'null' THEN RETURN CASE WHEN tagged THEN '["null"]' ELSE 'null' END;
    WHEN 'boolean' THEN body := v::text;
    WHEN 'number' THEN body := quote_string(trim_scale((v #>> '{}')::numeric)::text);
    WHEN 'string' THEN body := quote_string(v #>> '{}');
    WHEN 'array' THEN
        SELECT '['||coalesce(string_agg(flare_sealing.json_value(value,tagged),',' ORDER BY ord),'')||']'
        INTO body FROM jsonb_array_elements(v) WITH ORDINALITY AS a(value,ord);
    WHEN 'object' THEN
        SELECT coalesce(string_agg(CASE WHEN tagged THEN '['||quote_string(key)||','||flare_sealing.json_value(value,true)||']'
              ELSE quote_string(key)||':'||flare_sealing.json_value(value,false) END, ',' ORDER BY key COLLATE "C"),'')
        INTO body FROM jsonb_each(v);
        body := CASE WHEN tagged THEN '['||body||']' ELSE '{'||body||'}' END;
    END CASE;
    RETURN CASE WHEN tagged THEN '["'||k||'",'||body||']' ELSE body END;
END $$;
-- next function
CREATE FUNCTION flare_sealing.full_row(rel regclass, v jsonb) RETURNS text
LANGUAGE sql STABLE SET search_path = pg_catalog, flare_sealing SET timezone = 'UTC' AS $$
 SELECT '{'||string_agg(quote_string(attname)||':'||
   CASE WHEN atttypid='jsonb'::regtype THEN flare_sealing.json_value(v->attname,true)
        WHEN v->attname='null'::jsonb THEN 'null'
        WHEN atttypid='timestamptz'::regtype THEN quote_string(to_char((v->>attname)::timestamptz,'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))
        WHEN atttypid='bytea'::regtype THEN quote_string(encode((v->>attname)::bytea,'hex'))
        ELSE flare_sealing.json_value(v->attname,false) END, ',' ORDER BY attname::text COLLATE "C")||'}'
 FROM pg_attribute WHERE attrelid=rel AND attnum>0 AND NOT attisdropped
$$;
-- next function
CREATE FUNCTION flare_sealing.snapshot(target text, inv uuid, pid uuid)
RETURNS TABLE(member_counts jsonb, canonical_bytes bytea, member_digest text)
LANGUAGE plpgsql STABLE SET search_path = pg_catalog, flare_sealing SET timezone = 'UTC' SET datestyle = 'ISO, YMD' AS $$
DECLARE row_text text; part text; parts text[] := '{}'; n bigint; m record; predicate text;
BEGIN
    IF NOT EXISTS (SELECT FROM ownership() WHERE parent=target) THEN RAISE EXCEPTION 'Unknown seal target' USING ERRCODE='22023'; END IF;
    EXECUTE format('SELECT full_row(%L::regclass,to_jsonb(t)) FROM public.%I t WHERE investigation_id=$1 AND id=$2','public.'||target,target)
        INTO STRICT row_text USING inv,pid;
    member_counts := '{"parent":1}';
    FOR m IN SELECT * FROM ownership() WHERE parent=target ORDER BY child COLLATE "C" LOOP
        predicate := CASE WHEN m.child='protocol_unit_rule' THEN
            't.requirement_id IN (SELECT id FROM public.protocol_requirement WHERE investigation_id=$1 AND protocol_id=$2)'
            ELSE format('t.%I=$2',m.child_key) END;
        EXECUTE format('SELECT count(*),string_agg(''[''||quote_string(%L)||'',''||quote_string(t.investigation_id::text)||'',''||quote_string(t.id::text)||'',''||full_row(%L::regclass,to_jsonb(t))||'']'', '','' ORDER BY t.id) FROM public.%I t WHERE t.investigation_id=$1 AND %s',m.child,'public.'||m.child,m.child,predicate)
            INTO n,part USING inv,pid;
        member_counts := member_counts || jsonb_build_object(m.child,n);
        IF n>0 THEN parts := array_append(parts,part); END IF;
    END LOOP;
    canonical_bytes := convert_to('{"members":['||array_to_string(parts,',')||'],"parent":'||row_text||'}','UTF8');
    member_digest := encode(sha256(canonical_bytes),'hex');
    RETURN NEXT;
END $$;
-- next function
CREATE FUNCTION flare_sealing.lock_parent(target text, inv uuid, pid uuid) RETURNS void
LANGUAGE plpgsql SET search_path = pg_catalog, flare_sealing AS $$
DECLARE found_id uuid;
BEGIN
    IF current_setting('transaction_isolation') <> 'serializable' THEN
        RAISE EXCEPTION 'Aggregate writes require SERIALIZABLE' USING ERRCODE='25001';
    END IF;
    IF NOT EXISTS (SELECT FROM ownership() WHERE parent=target) THEN RAISE EXCEPTION 'Unknown aggregate' USING ERRCODE='22023'; END IF;
    PERFORM id FROM public.investigation WHERE id=inv FOR UPDATE;
    EXECUTE format('SELECT id FROM public.%I WHERE investigation_id=$1 AND id=$2 FOR UPDATE',target)
        INTO STRICT found_id USING inv,pid;
END $$;
-- next function
CREATE FUNCTION flare_sealing.lock_parents(targets jsonb) RETURNS void
LANGUAGE plpgsql SET search_path = pg_catalog, flare_sealing AS $$
DECLARE key record;
BEGIN
    -- Multi-aggregate operations reserve investigations first, then target rows.
    FOR key IN SELECT DISTINCT x.inv FROM jsonb_to_recordset(targets) x(inv uuid) ORDER BY x.inv LOOP
        PERFORM id FROM public.investigation WHERE id=key.inv FOR UPDATE;
    END LOOP;
    FOR key IN SELECT DISTINCT x.target COLLATE "C" AS target,x.pid,x.inv
        FROM jsonb_to_recordset(targets) x(target text,inv uuid,pid uuid) ORDER BY 1,2,3 LOOP
        PERFORM lock_parent(key.target,key.inv,key.pid);
    END LOOP;
END $$;
-- next function
CREATE FUNCTION flare_sealing.immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'Aggregate rows are append-only' USING ERRCODE='55000'; END $$;
-- next function
CREATE FUNCTION flare_sealing.guard_child() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, flare_sealing AS $$
DECLARE m record; pid uuid; saved public.aggregate_seal; actual record;
BEGIN
    SELECT * INTO STRICT m FROM ownership() WHERE child=TG_TABLE_NAME;
    pid := (to_jsonb(NEW)->>m.child_key)::uuid;
    IF m.child='protocol_unit_rule' THEN
        SELECT protocol_id INTO STRICT pid FROM public.protocol_requirement WHERE investigation_id=NEW.investigation_id AND id=pid;
    END IF;
    PERFORM lock_parent(m.parent,NEW.investigation_id,pid);
    EXECUTE format('SELECT * FROM public.aggregate_seal WHERE investigation_id=$1 AND %I=$2',m.seal_key)
        INTO saved USING NEW.investigation_id,pid;
    IF saved.id IS NOT NULL THEN
        IF TG_WHEN='BEFORE' THEN RAISE EXCEPTION 'Aggregate is already sealed' USING ERRCODE='55000'; END IF;
        SELECT * INTO STRICT actual FROM snapshot(m.parent,NEW.investigation_id,pid);
        IF (saved.member_counts,saved.member_digest) IS DISTINCT FROM (actual.member_counts,actual.member_digest) THEN
            RAISE EXCEPTION 'Final membership differs from seal' USING ERRCODE='23514';
        END IF;
    END IF;
    RETURN NEW;
END $$;
-- next function
CREATE FUNCTION flare_sealing.parse_shape(inv uuid, pid uuid) RETURNS void
LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE run parse_run; nr bigint; nf bigint; nc bigint;
BEGIN
    SELECT * INTO STRICT run FROM parse_run WHERE investigation_id=inv AND id=pid;
    SELECT count(*) INTO nr FROM source_record WHERE investigation_id=inv AND parse_run_id=pid;
    SELECT count(*) INTO nf FROM source_field WHERE investigation_id=inv AND parse_run_id=pid;
    SELECT count(*) INTO nc FROM observation WHERE investigation_id=inv AND parse_run_id=pid;
    IF run.status='failed' THEN
        IF nr+nf+nc>0 THEN RAISE EXCEPTION 'Failed run has children' USING ERRCODE='23514'; END IF;
    ELSIF nr<>run.record_count OR EXISTS (
        SELECT FROM source_record r WHERE r.investigation_id=inv AND r.parse_run_id=pid
        AND (NOT EXISTS (SELECT FROM source_field f WHERE f.investigation_id=inv AND f.parse_run_id=pid AND f.table_key=r.table_key)
          OR EXISTS (SELECT FROM source_field f WHERE f.investigation_id=inv AND f.parse_run_id=pid AND f.table_key=r.table_key
              AND NOT EXISTS (SELECT FROM observation o WHERE o.investigation_id=inv AND o.parse_run_id=pid
                  AND o.source_record_id=r.id AND o.source_field_id=f.id)))) OR EXISTS (
        SELECT FROM observation o JOIN source_record r ON (r.investigation_id,r.id)=(o.investigation_id,o.source_record_id)
        JOIN source_field f ON (f.investigation_id,f.id)=(o.investigation_id,o.source_field_id)
        WHERE o.investigation_id=inv AND o.parse_run_id=pid AND r.table_key<>f.table_key) THEN
        RAISE EXCEPTION 'Incomplete parse membership' USING ERRCODE='23514';
    END IF;
END $$;
-- next function
CREATE FUNCTION flare_sealing.check_parse() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    PERFORM flare_sealing.parse_shape(NEW.investigation_id,CASE WHEN TG_TABLE_NAME='parse_run' THEN NEW.id ELSE (to_jsonb(NEW)->>'parse_run_id')::uuid END);
    RETURN NULL;
END $$;
-- next function
CREATE FUNCTION flare_sealing.archive_matches(inv uuid, pid uuid, archive bytea) RETURNS void
LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE run parse_run; doc source_document; payload text; item jsonb; cell jsonb; rec source_record;
        headers jsonb; seen text[] := '{}'; ordinal bigint := 0; f record;
BEGIN
    PERFORM flare_sealing.parse_shape(inv,pid);
    SELECT * INTO STRICT run FROM parse_run WHERE investigation_id=inv AND id=pid;
    IF run.status<>'complete' OR archive IS NULL OR encode(sha256(archive),'hex')<>run.output_sha256 THEN
        RAISE EXCEPTION 'Parse archive absent, failed or hash mismatch' USING ERRCODE='23514';
    END IF;
    SELECT * INTO STRICT doc FROM source_document WHERE investigation_id=inv AND id=run.source_document_id;
    payload := convert_from(archive,'UTF8');
    IF right(payload,1)=chr(10) THEN payload := left(payload,-1); END IF;
    FOR item IN SELECT line::jsonb FROM unnest(string_to_array(payload,chr(10))) line LOOP
        ordinal := ordinal+1;
        SELECT * INTO rec FROM source_record WHERE investigation_id=inv AND parse_run_id=pid
            AND source_row_id=item#>>'{record_provenance,source_row_id}';
        IF NOT FOUND OR rec.source_row_id=ANY(seen) OR (item#>'{record_provenance,data_row_index}') IS DISTINCT FROM to_jsonb(ordinal)
            OR (item#>'{record_provenance,csv_record_number}') IS DISTINCT FROM to_jsonb(rec.source_record_number)
            OR item->>'parser_version' IS DISTINCT FROM run.parser_version
            OR item#>>'{source,filename}' IS DISTINCT FROM doc.original_filename
            OR item#>>'{source,sha256}' IS DISTINCT FROM doc.sha256 THEN
            RAISE EXCEPTION 'Archive record identity mismatch' USING ERRCODE='23514';
        END IF;
        seen := array_append(seen,rec.source_row_id);
        SELECT jsonb_agg(original_header ORDER BY sf.ordinal) INTO headers FROM source_field sf
            WHERE investigation_id=inv AND parse_run_id=pid AND table_key=rec.table_key;
        IF headers IS DISTINCT FROM item#>'{record_provenance,original_headers}' OR jsonb_typeof(item->'cells') IS DISTINCT FROM 'object'
            OR jsonb_array_length(headers)<>(SELECT count(*) FROM jsonb_object_keys(item->'cells')) THEN
            RAISE EXCEPTION 'Archive field membership mismatch' USING ERRCODE='23514';
        END IF;
        FOR f IN SELECT sf.ordinal,sf.original_header,o.raw_value,o.original_representation,o.parser_flags,o.parser_classification
            FROM source_field sf JOIN observation o ON (o.investigation_id,o.source_field_id)=(sf.investigation_id,sf.id)
            WHERE sf.investigation_id=inv AND o.source_record_id=rec.id LOOP
            cell := item->'cells'->f.original_header;
            IF headers->>(f.ordinal-1) IS DISTINCT FROM f.original_header OR cell IS NULL OR cell IS DISTINCT FROM f.original_representation
               OR cell->'raw_value' IS DISTINCT FROM coalesce(to_jsonb(f.raw_value),'null'::jsonb)
               OR cell->'column_index' IS DISTINCT FROM to_jsonb(f.ordinal)
               OR cell->>'original_header' IS DISTINCT FROM f.original_header
               OR cell->>'classification' IS DISTINCT FROM f.parser_classification
               OR f.parser_flags IS DISTINCT FROM jsonb_build_object('quality_flags',cell->'quality_flags') THEN
                RAISE EXCEPTION 'Archive cell content mismatch' USING ERRCODE='23514';
            END IF;
        END LOOP;
    END LOOP;
    IF ordinal<>run.record_count OR EXISTS (SELECT FROM source_field sf WHERE sf.investigation_id=inv AND sf.parse_run_id=pid
        AND NOT EXISTS (SELECT FROM source_record r WHERE r.investigation_id=inv AND r.parse_run_id=pid AND r.table_key=sf.table_key)) THEN
        RAISE EXCEPTION 'Archive does not witness all records and fields' USING ERRCODE='23514';
    END IF;
END $$;
-- next function
CREATE FUNCTION flare_sealing.check_seal() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, flare_sealing AS $$
DECLARE target text; pid uuid; actual record; archive_hex text;
BEGIN
    SELECT DISTINCT parent,(to_jsonb(NEW)->>seal_key)::uuid INTO STRICT target,pid
        FROM ownership() WHERE to_jsonb(NEW)->>seal_key IS NOT NULL;
    PERFORM lock_parent(target,NEW.investigation_id,pid);
    IF NEW.seal_version IS DISTINCT FROM 'canonical-json-v2' THEN
        RAISE EXCEPTION 'Unsupported seal version' USING ERRCODE='23514';
    END IF;
    IF target='parse_run' AND TG_WHEN='BEFORE' THEN
        archive_hex := current_setting('flare.parse_archive_hex',true);
        PERFORM archive_matches(NEW.investigation_id,pid,decode(archive_hex,'hex'));
    END IF;
    SELECT * INTO STRICT actual FROM snapshot(target,NEW.investigation_id,pid);
    IF actual.member_counts::text IS DISTINCT FROM NEW.member_counts::text OR actual.member_digest IS DISTINCT FROM NEW.member_digest THEN
        RAISE EXCEPTION 'Seal differs from aggregate membership' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
-- next function
CREATE FUNCTION flare_sealing.seal(target text, inv uuid, pid uuid, seal_id uuid, actor text, archive bytea DEFAULT NULL)
RETURNS public.aggregate_seal LANGUAGE plpgsql SET search_path = pg_catalog, flare_sealing AS $$
DECLARE actual record; saved public.aggregate_seal; target_key text;
BEGIN
    PERFORM lock_parent(target,inv,pid);
    SELECT DISTINCT seal_key INTO STRICT target_key FROM ownership() WHERE parent=target;
    -- Idempotent retry, under the same parent lock. Never replace an earlier seal.
    EXECUTE format('SELECT * FROM public.aggregate_seal WHERE investigation_id=$1 AND %I=$2',target_key)
        INTO saved USING inv,pid;
    IF saved.id IS NOT NULL THEN RETURN saved; END IF;
    SELECT * INTO STRICT actual FROM snapshot(target,inv,pid);
    IF target='parse_run' THEN
        PERFORM archive_matches(inv,pid,archive);
        PERFORM set_config('flare.parse_archive_hex',encode(archive,'hex'),true);
    END IF;
    EXECUTE format('INSERT INTO public.aggregate_seal(investigation_id,id,%I,seal_version,member_counts,member_digest,sealed_by,created_at)
        VALUES($1,$2,$3,''canonical-json-v2'',$4,$5,$6,transaction_timestamp()) RETURNING *',target_key)
        INTO saved USING inv,seal_id,pid,actual.member_counts,actual.member_digest,actor;
    IF target='parse_run' THEN PERFORM set_config('flare.parse_archive_hex','',true); END IF;
    RETURN saved;
END $$;
