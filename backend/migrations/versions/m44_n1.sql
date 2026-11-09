-- A row per semantic scope fact. The highest revision wins even when unsealed.
CREATE FUNCTION flare_n1.facts(inv uuid, result_key uuid)
RETURNS TABLE(kind text, obs uuid, link_id uuid, issue_id uuid, head uuid, head_seal uuid,
              decision text, test_id uuid, severity text)
LANGUAGE sql STABLE SET search_path=pg_catalog,public,pg_temp AS $$
 WITH observations AS (
   SELECT a.observation_id AS id FROM result_input i JOIN semantic_annotation a
     ON (a.investigation_id,a.id)=(i.investigation_id,i.annotation_id)
   WHERE i.investigation_id=inv AND i.result_id=result_key
   UNION
   SELECT a.observation_id FROM result_condition c JOIN condition_component k
     ON (k.investigation_id,k.condition_id)=(c.investigation_id,c.condition_id)
   JOIN semantic_annotation a ON (a.investigation_id,a.id)=(k.investigation_id,k.annotation_id)
   WHERE c.investigation_id=inv AND c.result_id=result_key
 ), links AS (
   SELECT o.id AS obs,l.id,l.experimental_test_id AS test_id,h.id AS head,h.decision,s.id AS seal
   FROM observations o JOIN observation v ON (v.investigation_id,v.id)=(inv,o.id)
   JOIN test_source_record l ON (l.investigation_id,l.source_record_id)=(inv,v.source_record_id)
   LEFT JOIN LATERAL (SELECT r.id,r.decision FROM review_event r
     WHERE r.investigation_id=inv AND r.test_link_id=l.id ORDER BY r.revision DESC LIMIT 1) h ON true
   LEFT JOIN aggregate_seal s ON (s.investigation_id,s.review_id)=(inv,h.id)
 ), issues AS (
   SELECT o.id AS obs,q.id,q.severity FROM observations o JOIN data_quality_issue q
     ON (q.investigation_id,q.observation_id)=(inv,o.id)
   UNION
   SELECT l.obs,q.id,q.severity FROM links l JOIN data_quality_issue q
     ON (q.investigation_id,q.experimental_test_id)=(inv,l.test_id)
   WHERE l.decision='approved' AND l.seal IS NOT NULL
 )
 SELECT 'scope_observation',o.id,NULL::uuid,NULL::uuid,NULL::uuid,NULL::uuid,NULL::text,NULL::uuid,NULL::text FROM observations o
 UNION ALL SELECT 'scope_link',l.obs,l.id,NULL,l.head,l.seal,l.decision,l.test_id,NULL FROM links l
 UNION ALL SELECT 'scope_issue',q.obs,NULL,q.id,h.id,s.id,h.decision,NULL,q.severity FROM issues q
 LEFT JOIN LATERAL (SELECT r.id,r.decision FROM review_event r WHERE r.investigation_id=inv AND r.issue_id=q.id
                    ORDER BY r.revision DESC LIMIT 1) h ON true
 LEFT JOIN aggregate_seal s ON (s.investigation_id,s.review_id)=(inv,h.id)
$$;
-- next function
CREATE FUNCTION flare_n1.expected(inv uuid, result_key uuid)
RETURNS TABLE(kind text, role text, obs uuid, link_id uuid, issue_id uuid, head uuid, head_seal uuid, dependency uuid)
LANGUAGE sql STABLE AS $$
 WITH f AS MATERIALIZED (SELECT * FROM flare_n1.facts(inv,result_key))
 SELECT f.kind,f.kind,f.obs,f.link_id,f.issue_id,f.head,f.head_seal,NULL::uuid FROM f
 UNION
 SELECT 'decision',CASE f.kind WHEN 'scope_link' THEN 'applicability_identity' ELSE 'applicability_clearance' END,
 NULL,NULL,NULL,NULL,NULL,f.head FROM f WHERE f.head_seal IS NOT NULL AND
 ((f.kind='scope_link' AND f.decision='approved') OR (f.severity IN ('review','blocking') AND f.decision='resolved'))
$$;
-- next function
CREATE FUNCTION flare_n1.stored(inv uuid, owner_id uuid)
RETURNS TABLE(kind text, role text, obs uuid, link_id uuid, issue_id uuid, head uuid, head_seal uuid, dependency uuid)
LANGUAGE sql STABLE AS $$
 SELECT d.entry_kind,d.role,d.snapshot_observation_id,d.snapshot_link_id,d.snapshot_issue_id,
 d.snapshot_review_id,d.snapshot_review_seal_id,d.dependency_review_id FROM public.approval_dependency d
 WHERE d.investigation_id=inv AND d.owner_review_id=owner_id
 AND (d.entry_kind<>'decision' OR d.role IN ('applicability_identity','applicability_clearance'))
$$;
-- next function
CREATE FUNCTION flare_n1.matches(inv uuid, owner_id uuid) RETURNS boolean
LANGUAGE sql STABLE SET search_path=pg_catalog,public,pg_temp AS $$
 WITH owner AS (SELECT r.* FROM review_event r WHERE r.investigation_id=inv AND r.id=owner_id AND r.result_id IS NOT NULL
   AND r.decision='approved' AND r.applicability_policy_version='identity-issue-snapshot-v1' AND r.applicability_unresolved_count=0),
 want AS (SELECT e.* FROM owner r CROSS JOIN LATERAL flare_n1.expected(inv,r.result_id) e),
 have AS (SELECT * FROM flare_n1.stored(inv,owner_id)),
 f AS (SELECT x.* FROM owner r CROSS JOIN LATERAL flare_n1.facts(inv,r.result_id) x)
 SELECT EXISTS(SELECT FROM owner r JOIN aggregate_seal s ON (s.investigation_id,s.result_id)=(inv,r.result_id))
 AND NOT EXISTS ((TABLE want EXCEPT ALL TABLE have) UNION ALL (TABLE have EXCEPT ALL TABLE want))
 AND NOT EXISTS (SELECT FROM f WHERE severity IN ('review','blocking') AND
              (decision IS DISTINCT FROM 'resolved' OR head_seal IS NULL))
 AND NOT EXISTS (SELECT FROM owner r JOIN result_input i ON (i.investigation_id,i.result_id)=(inv,r.result_id)
   JOIN semantic_annotation a ON (a.investigation_id,a.id)=(inv,i.annotation_id)
   JOIN condition_segment seg ON (seg.investigation_id,seg.id)=(inv,i.segment_id)
   WHERE NOT EXISTS (SELECT FROM f WHERE f.obs=a.observation_id AND f.link_id=i.test_link_id
      AND f.test_id=seg.experimental_test_id AND f.head=i.test_link_review_id AND f.decision='approved' AND f.head_seal IS NOT NULL))
 AND NOT EXISTS (SELECT FROM owner r JOIN result_condition c ON (c.investigation_id,c.result_id)=(inv,r.result_id)
   JOIN experimental_condition ec ON (ec.investigation_id,ec.id)=(inv,c.condition_id)
   JOIN analytical_eligibility e ON (e.investigation_id,e.id)=(inv,c.eligibility_id)
   WHERE NOT EXISTS (SELECT FROM aggregate_seal WHERE investigation_id=inv AND condition_id=c.condition_id)
   OR EXISTS (SELECT FROM condition_component k JOIN semantic_annotation a ON (a.investigation_id,a.id)=(inv,k.annotation_id)
      WHERE k.investigation_id=inv AND k.condition_id=c.condition_id AND NOT EXISTS (
        SELECT FROM f JOIN approval_dependency d ON d.investigation_id=inv AND d.owner_review_id=e.condition_review_id
          AND d.entry_kind='decision' AND d.dependency_review_id=f.head
        JOIN review_event cr ON (cr.investigation_id,cr.id)=(inv,d.owner_review_id) AND cr.condition_id=ec.id AND cr.decision='approved'
        JOIN aggregate_seal cs ON (cs.investigation_id,cs.review_id)=(inv,cr.id)
        WHERE f.obs=a.observation_id AND f.test_id=ec.experimental_test_id AND f.decision='approved' AND f.head_seal IS NOT NULL
        AND e.experimental_test_id=ec.experimental_test_id AND e.condition_id=c.condition_id)))
 -- Every identity review selected by a condition must be effective for one of
 -- that condition's consumed components. A different valid pin cannot mask it.
 AND NOT EXISTS (SELECT FROM owner r JOIN result_condition c ON (c.investigation_id,c.result_id)=(inv,r.result_id)
   JOIN experimental_condition ec ON (ec.investigation_id,ec.id)=(inv,c.condition_id)
   JOIN analytical_eligibility e ON (e.investigation_id,e.id)=(inv,c.eligibility_id)
   JOIN approval_dependency d ON (d.investigation_id,d.owner_review_id)=(inv,e.condition_review_id) AND d.entry_kind='decision'
   JOIN review_event pinned ON (pinned.investigation_id,pinned.id)=(inv,d.dependency_review_id) AND pinned.test_link_id IS NOT NULL
   WHERE NOT EXISTS (SELECT FROM condition_component k JOIN semantic_annotation a
     ON (a.investigation_id,a.id)=(inv,k.annotation_id)
     JOIN f ON f.obs=a.observation_id AND f.head=pinned.id AND f.link_id=pinned.test_link_id
     WHERE k.investigation_id=inv AND k.condition_id=ec.id AND f.test_id=ec.experimental_test_id
       AND f.decision='approved' AND f.head_seal IS NOT NULL))
$$;
-- next function
CREATE FUNCTION flare_n1.historical(inv uuid, owner_id uuid, pinned_seal uuid)
RETURNS TABLE(investigation_id uuid, result_id uuid, result_review_id uuid, review_seal_id uuid, owner_revision integer, predecessor uuid, policy text, unresolved_count integer, digest text, entry_id uuid,
 kind text, role text, observation_id uuid, source_row uuid, link_id uuid, associated_test uuid, effective_test uuid,
 issue_id uuid, issue_severity text, issue_test uuid, head uuid, decision text, head_seal uuid, dependency uuid)
LANGUAGE sql STABLE SET search_path=pg_catalog,public,pg_temp AS $$
 SELECT r.investigation_id,r.result_id,r.id,s.id,r.revision,r.supersedes_id,r.applicability_policy_version,r.applicability_unresolved_count,s.member_digest,d.id,
 d.entry_kind,d.role,d.snapshot_observation_id,o.source_record_id,l.id,l.experimental_test_id,
 CASE WHEN h.decision='approved' AND d.snapshot_review_seal_id IS NOT NULL THEN l.experimental_test_id END,
 q.id,q.severity,q.experimental_test_id,d.snapshot_review_id,h.decision,d.snapshot_review_seal_id,d.dependency_review_id
 FROM review_event r JOIN aggregate_seal s ON (s.investigation_id,s.review_id,s.id)=(inv,r.id,pinned_seal)
 LEFT JOIN approval_dependency d ON (d.investigation_id,d.owner_review_id)=(inv,r.id)
 LEFT JOIN observation o ON (o.investigation_id,o.id)=(inv,d.snapshot_observation_id)
 LEFT JOIN test_source_record l ON (l.investigation_id,l.id)=(inv,d.snapshot_link_id)
 LEFT JOIN data_quality_issue q ON (q.investigation_id,q.id)=(inv,d.snapshot_issue_id)
 LEFT JOIN review_event h ON (h.investigation_id,h.id)=(inv,d.snapshot_review_id)
 WHERE r.investigation_id=inv AND r.id=owner_id AND r.result_id IS NOT NULL AND r.decision='approved'
 ORDER BY d.id
$$;
-- next function
CREATE FUNCTION flare_n1.applicability_current(inv uuid, owner_id uuid) RETURNS boolean
LANGUAGE sql STABLE AS $$
 SELECT EXISTS(SELECT FROM public.aggregate_seal WHERE investigation_id=inv AND review_id=owner_id)
 AND flare_n1.matches(inv,owner_id)
$$;
-- next function
CREATE FUNCTION flare_n1.build(inv uuid, owner_id uuid, seal_id uuid, actor text) RETURNS uuid
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE result_key uuid; previous uuid;
BEGIN
 PERFORM flare_sealing.lock_parent('review_event',inv,owner_id);
 SELECT r.result_id INTO STRICT result_key FROM review_event r WHERE r.investigation_id=inv AND r.id=owner_id
 AND r.result_id IS NOT NULL AND r.decision='approved';
 SELECT id INTO previous FROM aggregate_seal WHERE investigation_id=inv AND review_id=owner_id;
 IF previous IS NOT NULL THEN
   IF NOT flare_n1.matches(inv,owner_id) THEN RAISE EXCEPTION 'Snapshot requires successor approval' USING ERRCODE='23514'; END IF;
   RETURN previous;
 END IF;
 INSERT INTO approval_dependency(investigation_id,id,owner_review_id,entry_kind,role,snapshot_observation_id,snapshot_link_id,
   snapshot_issue_id,snapshot_review_id,snapshot_review_seal_id,dependency_review_id,created_at)
 SELECT inv,gen_random_uuid(),owner_id,e.kind,e.role,e.obs,e.link_id,e.issue_id,e.head,e.head_seal,e.dependency,transaction_timestamp()
 FROM flare_n1.expected(inv,result_key) e;
 IF NOT flare_n1.matches(inv,owner_id) THEN RAISE EXCEPTION 'Invalid N1 applicability or unresolved issue' USING ERRCODE='23514'; END IF;
 RETURN (flare_sealing.seal('review_event',inv,owner_id,seal_id,actor)).id;
END $$;
-- next function
CREATE FUNCTION flare_n1.lock_write() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE subject_col text; subject_id uuid; prev review_event;
BEGIN
 IF current_setting('transaction_isolation')<>'serializable' THEN
   RAISE EXCEPTION 'N1 writes require SERIALIZABLE' USING ERRCODE='25001';
 END IF;
 PERFORM id FROM investigation WHERE id=NEW.investigation_id FOR UPDATE;
 -- Paired predicate read for SSI: writers inspect the review-seal range, while
 -- certification reads the candidate-link, issue and head ranges.
 PERFORM id FROM aggregate_seal WHERE investigation_id=NEW.investigation_id AND review_id IS NOT NULL;
 IF TG_TABLE_NAME='review_event' THEN
   IF NEW.test_link_id IS NOT NULL THEN
      subject_col:='test_link_id'; subject_id:=NEW.test_link_id;
      PERFORM id FROM test_source_record WHERE investigation_id=NEW.investigation_id AND id=subject_id FOR UPDATE;
   ELSIF NEW.issue_id IS NOT NULL THEN
      subject_col:='issue_id'; subject_id:=NEW.issue_id;
      PERFORM id FROM data_quality_issue WHERE investigation_id=NEW.investigation_id AND id=subject_id FOR UPDATE;
   ELSIF NEW.result_id IS NOT NULL THEN
      subject_col:='result_id'; subject_id:=NEW.result_id;
      PERFORM id FROM analytical_result WHERE investigation_id=NEW.investigation_id AND id=subject_id FOR UPDATE;
   END IF;
   IF subject_col IS NOT NULL THEN
      EXECUTE format('SELECT * FROM public.review_event WHERE investigation_id=$1 AND %I=$2 ORDER BY revision DESC LIMIT 1',subject_col)
        INTO prev USING NEW.investigation_id,subject_id;
      IF NEW.revision<>coalesce(prev.revision,0)+1 OR NEW.supersedes_id IS DISTINCT FROM prev.id THEN
         RAISE EXCEPTION 'Review predecessor differs from subject head' USING ERRCODE='23514';
      END IF;
      IF (subject_col='issue_id' AND NEW.decision NOT IN ('open','resolved')) OR
         (subject_col<>'issue_id' AND NEW.decision IN ('open','resolved')) THEN
         RAISE EXCEPTION 'Invalid N1 subject decision' USING ERRCODE='23514';
      END IF;
   END IF;
 END IF;
 RETURN NEW;
END $$;
-- next function
CREATE FUNCTION flare_n1.check_owner() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
BEGIN
 IF (NEW.entry_kind<>'decision' OR NEW.role IN ('applicability_identity','applicability_clearance'))
 AND NOT EXISTS (SELECT FROM review_event WHERE investigation_id=NEW.investigation_id AND id=NEW.owner_review_id
                 AND result_id IS NOT NULL AND decision='approved') THEN
    RAISE EXCEPTION 'N1 member requires a result approval owner' USING ERRCODE='23514';
 END IF;
 RETURN NEW;
END $$;
-- next function
CREATE FUNCTION flare_n1.certify() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE owner_key uuid; pos point;
BEGIN
 IF TG_TABLE_NAME='review_event' THEN owner_key:=NEW.id; ELSE owner_key:=NEW.review_id; END IF;
 IF NOT EXISTS (SELECT FROM review_event WHERE investigation_id=NEW.investigation_id AND id=owner_key
        AND result_id IS NOT NULL AND decision='approved') THEN RETURN NULL; END IF;
 SELECT s.ctid::text::point INTO pos FROM aggregate_seal s
 WHERE s.investigation_id=NEW.investigation_id AND s.review_id=owner_key;
 IF pos IS NULL OR NOT flare_n1.matches(NEW.investigation_id,owner_key) THEN
    RAISE EXCEPTION 'Final result review lacks complete sealed N1 attestation' USING ERRCODE='23514';
 END IF;
 -- A transaction-level marker survives SET CONSTRAINTS ... IMMEDIATE and cannot
 -- be released by pg_advisory_unlock. A seal tuple cannot move while this writer
 -- holds its relation lock. The slot is used only during this transaction.
 PERFORM pg_advisory_xact_lock_shared(pos[0]::bigint::bit(32)::integer,1444000000+pos[1]::integer);
 RETURN NULL;
END $$;
-- next function
CREATE FUNCTION flare_n1.recheck_new() RETURNS trigger
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE owner_key uuid;
BEGIN
 -- Only this backend's newly certified seals need final-view validation.
 -- Never revalidate old committed snapshots on an unrelated future write.
 FOR owner_key IN SELECT s.review_id FROM pg_locks l JOIN aggregate_seal s
   ON l.classid::bigint=(s.ctid::text::point)[0]::bigint
   AND l.objid::bigint=1444000000+(s.ctid::text::point)[1]::integer
   WHERE l.locktype='advisory' AND l.pid=pg_backend_pid() AND l.objsubid=2 AND l.granted
     AND s.investigation_id=NEW.investigation_id AND s.review_id IS NOT NULL LOOP
   IF NOT flare_n1.matches(NEW.investigation_id,owner_key) THEN
      RAISE EXCEPTION 'N1 scope changed in the certification transaction' USING ERRCODE='23514';
   END IF;
 END LOOP;
 RETURN NULL;
END $$;
-- next function
CREATE FUNCTION flare_n1.append_head(inv uuid, subject_kind text, subject uuid, review_key uuid,
 new_decision text, evidence uuid, reviewer text, reason text) RETURNS uuid
LANGUAGE plpgsql SET search_path=pg_catalog,public,pg_temp AS $$
DECLARE col text; prev review_event; conflict text;
BEGIN
 IF current_setting('transaction_isolation')<>'serializable' THEN
    RAISE EXCEPTION 'N1 review append requires SERIALIZABLE' USING ERRCODE='25001';
 END IF;
 col:=CASE subject_kind WHEN 'link' THEN 'test_link_id' WHEN 'issue' THEN 'issue_id' WHEN 'result' THEN 'result_id' END;
 IF col IS NULL THEN RAISE EXCEPTION 'Unknown N1 subject' USING ERRCODE='22023'; END IF;
 PERFORM id FROM investigation WHERE id=inv FOR UPDATE;
 EXECUTE format('SELECT * FROM review_event WHERE investigation_id=$1 AND %I=$2 ORDER BY revision DESC LIMIT 1',col)
    INTO prev USING inv,subject;
 BEGIN
    INSERT INTO review_event(investigation_id,id,test_link_id,issue_id,result_id,revision,supersedes_id,decision,
        evidence_id,reviewer_ref,rationale,created_at,reviewed_at,applicability_policy_version,applicability_unresolved_count)
    VALUES(inv,review_key,CASE WHEN subject_kind='link' THEN subject END,CASE WHEN subject_kind='issue' THEN subject END,
        CASE WHEN subject_kind='result' THEN subject END,coalesce(prev.revision,0)+1,prev.id,new_decision,
        evidence,reviewer,reason,transaction_timestamp(),transaction_timestamp(),
        CASE WHEN subject_kind='result' AND new_decision='approved' THEN 'identity-issue-snapshot-v1' END,
        CASE WHEN subject_kind='result' AND new_decision='approved' THEN 0 END);
 EXCEPTION WHEN unique_violation THEN
    GET STACKED DIAGNOSTICS conflict=CONSTRAINT_NAME;
    -- The revision and predecessor came from the very same SERIALIZABLE view.
    -- A sibling append can win the unique index before SSI reports the conflict.
    IF conflict IN ('uq_review_event_01','uq_review_event_05','uq_review_event_07','uq_review_event_08') THEN
       RAISE EXCEPTION 'Concurrent N1 review append; retry entire transaction' USING ERRCODE='40001';
    END IF;
    RAISE;
 END;
 RETURN review_key;
END $$;
