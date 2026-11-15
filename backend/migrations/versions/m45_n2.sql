CREATE FUNCTION flare_sealing.check_condition_review() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    rev public.review_event;
    comp record;
    var_rev public.review_event;
    v_head record;
    c_head record;
    dep_seal public.aggregate_seal;
    var_seal public.aggregate_seal;
BEGIN
    IF NEW.review_id IS NULL THEN
        RETURN NEW;
    END IF;

    SELECT * INTO rev FROM public.review_event
        WHERE investigation_id = NEW.investigation_id AND id = NEW.review_id;
    
    IF rev.condition_id IS NOT NULL AND rev.decision = 'approved' THEN
        -- 1. Condition review being sealed must be the current applicable review head for this condition
        SELECT r.id, r.revision INTO c_head
        FROM public.review_event r
        WHERE r.investigation_id = NEW.investigation_id AND r.condition_id = rev.condition_id
        ORDER BY r.revision DESC LIMIT 1;

        IF rev.id <> c_head.id THEN
            RAISE EXCEPTION 'Condition review being sealed is superseded by revision %', c_head.revision USING ERRCODE = '23514';
        END IF;

        -- 2. Exact condition_content seal dependency is strictly mandatory (even with 0 components)
        SELECT s.* INTO dep_seal
        FROM public.approval_dependency d
        JOIN public.aggregate_seal s ON (s.investigation_id, s.id) = (d.investigation_id, d.dependency_seal_id)
        WHERE d.investigation_id = NEW.investigation_id
          AND d.owner_review_id = rev.id
          AND d.entry_kind = 'decision'
          AND d.role = 'condition_content'
          AND s.condition_id = rev.condition_id;
        
        IF dep_seal.id IS NULL THEN
            RAISE EXCEPTION 'Approved condition review lacks sealed condition_content dependency' USING ERRCODE = '23514';
        END IF;

        -- 3. Every referenced variable in condition_component must have an approved, sealed, current variable_definition review
        FOR comp IN
            SELECT DISTINCT k.variable_id, v.variable_code, v.definition_version
            FROM public.condition_component k
            JOIN public.scientific_variable v ON (v.investigation_id, v.id) = (k.investigation_id, k.variable_id)
            WHERE k.investigation_id = NEW.investigation_id AND k.condition_id = rev.condition_id
        LOOP
            SELECT vr.* INTO var_rev
            FROM public.approval_dependency d
            JOIN public.review_event vr ON (vr.investigation_id, vr.id) = (d.investigation_id, d.dependency_review_id)
            WHERE d.investigation_id = NEW.investigation_id
              AND d.owner_review_id = rev.id
              AND d.entry_kind = 'decision'
              AND d.role = 'variable_definition'
              AND vr.variable_id = comp.variable_id;
            
            IF var_rev.id IS NULL THEN
                RAISE EXCEPTION 'Approved condition review lacks variable_definition dependency for variable % (version %)',
                    comp.variable_code, comp.definition_version USING ERRCODE = '23514';
            END IF;

            IF var_rev.decision <> 'approved' THEN
                RAISE EXCEPTION 'Variable definition review for % is not approved (decision: %)',
                    comp.variable_code, var_rev.decision USING ERRCODE = '23514';
            END IF;

            SELECT * INTO var_seal
            FROM public.aggregate_seal
            WHERE investigation_id = NEW.investigation_id AND review_id = var_rev.id;

            IF var_seal.id IS NULL THEN
                RAISE EXCEPTION 'Variable definition review for % is not sealed', comp.variable_code USING ERRCODE = '23514';
            END IF;

            SELECT r.id, r.revision, r.decision INTO v_head
            FROM public.review_event r
            WHERE r.investigation_id = NEW.investigation_id AND r.variable_id = comp.variable_id
            ORDER BY r.revision DESC LIMIT 1;

            IF var_rev.id <> v_head.id THEN
                RAISE EXCEPTION 'Variable definition review for % is superseded (pinned rev %, current head rev %)',
                    comp.variable_code, var_rev.revision, v_head.revision USING ERRCODE = '23514';
            END IF;
        END LOOP;
    END IF;

    RETURN NEW;
END $$;
-- next function
CREATE FUNCTION flare_n2.validate_result(inv uuid, result_key uuid)
RETURNS TABLE(rule text, passed boolean, detail text)
LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    res public.analytical_result;
    prot public.analysis_protocol;
    c_count integer;
    input_count integer;
    input_req_count integer;
    all_input_waived boolean;
    res_cond_count integer;
    bad_inputs integer;
    bad_segments integer;
    bad_cardinality integer;
    bad_cond_scope integer;
    bad_cond_integrity integer;
    missing_active_components integer;
    missing_condition_roles integer;
BEGIN
    SELECT * INTO res FROM public.analytical_result WHERE investigation_id = inv AND id = result_key;
    IF res.id IS NULL THEN
        RETURN QUERY SELECT 'result_exists'::text, false, 'AnalyticalResult row not found'::text;
        RETURN;
    END IF;

    SELECT * INTO prot FROM public.analysis_protocol WHERE investigation_id = inv AND id = res.protocol_id;
    IF prot.id IS NULL OR prot.requirements_schema_version <> 'relational-v1' THEN
        RETURN QUERY SELECT 'protocol_schema'::text, false, 'Protocol missing or requirements_schema_version <> relational-v1'::text;
        RETURN;
    ELSE
        RETURN QUERY SELECT 'protocol_schema'::text, true, 'requirements_schema_version is relational-v1'::text;
    END IF;

    SELECT count(*) INTO input_req_count FROM public.protocol_requirement
        WHERE investigation_id = inv AND protocol_id = res.protocol_id AND target_kind = 'input';
    IF input_req_count = 0 THEN
        RETURN QUERY SELECT 'input_requirements_present'::text, false, 'Protocol contains zero input requirements'::text;
        RETURN;
    ELSE
        RETURN QUERY SELECT 'input_requirements_present'::text, true, format('Protocol has %s input requirements', input_req_count);
    END IF;

    SELECT count(*) INTO input_count FROM public.result_input
        WHERE investigation_id = inv AND result_id = result_key;
    IF input_count = 0 THEN
        RETURN QUERY SELECT 'result_inputs_present'::text, false, 'AnalyticalResult contains zero inputs'::text;
        RETURN;
    ELSE
        RETURN QUERY SELECT 'result_inputs_present'::text, true, format('AnalyticalResult has %s inputs', input_count);
    END IF;

    -- Validate each result input against its requirement, unit rule, value policy, and phase
    SELECT count(*) INTO bad_inputs
    FROM public.result_input i
    JOIN public.semantic_annotation a ON (a.investigation_id, a.id) = (inv, i.annotation_id)
    JOIN public.scientific_variable v ON (v.investigation_id, v.id) = (inv, a.variable_id)
    LEFT JOIN public.protocol_requirement req ON (req.investigation_id, req.protocol_id, req.target_kind, req.requirement_key) =
                                                 (inv, res.protocol_id, 'input', i.input_role)
    WHERE i.investigation_id = inv AND i.result_id = result_key
      AND (
          req.id IS NULL
          OR req.variable_id <> a.variable_id
          OR (req.phase <> 'not_applicable' AND req.phase IS DISTINCT FROM a.observed_phase)
          OR (req.value_policy = 'numeric_only' AND (a.value_kind <> 'numeric' OR a.numeric_value IS NULL))
          OR (req.value_policy = 'categorical' AND a.value_kind <> 'text')
          OR (req.value_policy = 'numeric_or_censored' AND a.value_kind NOT IN ('numeric', 'censored'))
          OR NOT EXISTS (
              SELECT 1 FROM public.protocol_unit_rule u
              WHERE u.investigation_id = inv AND u.requirement_id = req.id
                AND (
                    (u.unit_text = a.interpreted_unit AND u.unit_basis = v.unit_basis)
                    OR (u.unit_text = 'not_applicable' AND a.interpreted_unit IS NULL)
                )
                AND u.method = a.transformation_method
                AND u.method_version = a.transformation_version
          )
      );

    IF bad_inputs > 0 THEN
        RETURN QUERY SELECT 'inputs_match_requirements'::text, false, format('%s inputs fail requirement/unit/policy matching', bad_inputs);
    ELSE
        RETURN QUERY SELECT 'inputs_match_requirements'::text, true, 'All inputs match requirements, unit rules, value policies and phases';
    END IF;

    -- Validate input segment belongs to the linked test
    SELECT count(*) INTO bad_segments
    FROM public.result_input i
    JOIN public.condition_segment seg ON (seg.investigation_id, seg.id) = (inv, i.segment_id)
    JOIN public.test_source_record l ON (l.investigation_id, l.id) = (inv, i.test_link_id)
    WHERE i.investigation_id = inv AND i.result_id = result_key
      AND seg.experimental_test_id <> l.experimental_test_id;

    IF bad_segments > 0 THEN
        RETURN QUERY SELECT 'input_segment_coverage'::text, false, format('%s inputs have segment not belonging to linked test', bad_segments);
    ELSE
        RETURN QUERY SELECT 'input_segment_coverage'::text, true, 'All inputs belong to documented segments of linked tests';
    END IF;

    -- Validate input cardinality per (test, segment)
    SELECT count(*) INTO bad_cardinality
    FROM (
        SELECT req.id AS req_id, seg.experimental_test_id, i.segment_id, count(i.id) AS actual_count, req.min_count, req.max_count
        FROM public.protocol_requirement req
        CROSS JOIN (
            SELECT DISTINCT l.experimental_test_id, inp.segment_id
            FROM public.result_input inp
            JOIN public.test_source_record l ON (l.investigation_id, l.id) = (inv, inp.test_link_id)
            WHERE inp.investigation_id = inv AND inp.result_id = result_key
        ) seg
        LEFT JOIN public.result_input i ON i.investigation_id = inv AND i.result_id = result_key
                                       AND i.input_role = req.requirement_key
                                       AND i.segment_id = seg.segment_id
        WHERE req.investigation_id = inv AND req.protocol_id = res.protocol_id AND req.target_kind = 'input'
        GROUP BY req.id, seg.experimental_test_id, i.segment_id, req.min_count, req.max_count
    ) c
    WHERE c.actual_count < c.min_count OR c.actual_count > c.max_count;

    IF bad_cardinality > 0 THEN
        RETURN QUERY SELECT 'input_cardinality'::text, false, format('%s input requirement cardinality violations per (test, segment)', bad_cardinality);
    ELSE
        RETURN QUERY SELECT 'input_cardinality'::text, true, 'Input cardinality constraints satisfied for all (test, segment) pairs';
    END IF;

    -- 12-Case Truth Table Evaluation
    SELECT count(*) INTO c_count
    FROM public.protocol_requirement
    WHERE investigation_id = inv AND protocol_id = res.protocol_id AND target_kind = 'condition';

    SELECT count(*) = 0 INTO all_input_waived
    FROM public.protocol_requirement
    WHERE investigation_id = inv AND protocol_id = res.protocol_id AND target_kind = 'input'
      AND (instrument_policy <> 'not_required' OR stability_policy <> 'not_applicable');

    SELECT count(*) INTO res_cond_count
    FROM public.result_condition
    WHERE investigation_id = inv AND result_id = result_key;

    IF res_cond_count = 0 THEN
        IF c_count = 0 AND all_input_waived THEN
            RETURN QUERY SELECT 'empty_condition_validity'::text, true, 'Empty ResultCondition valid (C=0, all input policies waived)';
        ELSE
            RETURN QUERY SELECT 'empty_condition_validity'::text, false, format('Empty ResultCondition invalid (C=%s, all_input_waived=%s)', c_count, all_input_waived);
        END IF;
    ELSE
        RETURN QUERY SELECT 'empty_condition_validity'::text, true, format('Non-empty ResultCondition provided (%s conditions)', res_cond_count);
    END IF;

    IF res_cond_count > 0 THEN
        -- Every result condition must belong to an input test/segment
        SELECT count(*) INTO bad_cond_scope
        FROM public.result_condition rc
        JOIN public.experimental_condition ec ON (ec.investigation_id, ec.id) = (inv, rc.condition_id)
        WHERE rc.investigation_id = inv AND rc.result_id = result_key
          AND NOT EXISTS (
              SELECT 1 FROM public.result_input i
              JOIN public.condition_segment seg ON (seg.investigation_id, seg.id) = (inv, i.segment_id)
              WHERE i.investigation_id = inv AND i.result_id = result_key
                AND seg.experimental_test_id = ec.experimental_test_id
                AND i.segment_id = ec.segment_id
          );

        IF bad_cond_scope > 0 THEN
            RETURN QUERY SELECT 'condition_scope_coverage'::text, false, format('%s conditions do not match any input (test, segment)', bad_cond_scope);
        ELSE
            RETURN QUERY SELECT 'condition_scope_coverage'::text, true, 'All conditions correspond to input (test, segment) scopes';
        END IF;

        -- Validate condition integrity, seals, eligibility and approval lineage
        SELECT count(*) INTO bad_cond_integrity
        FROM public.result_condition rc
        JOIN public.experimental_condition ec ON (ec.investigation_id, ec.id) = (inv, rc.condition_id)
        JOIN public.analytical_eligibility ae ON (ae.investigation_id, ae.id) = (inv, rc.eligibility_id)
        LEFT JOIN public.aggregate_seal cs ON (cs.investigation_id, cs.condition_id) = (inv, ec.id)
        LEFT JOIN public.review_event cr ON (cr.investigation_id, cr.id) = (inv, ae.condition_review_id)
        LEFT JOIN public.aggregate_seal crs ON (crs.investigation_id, crs.review_id) = (inv, cr.id)
        WHERE rc.investigation_id = inv AND rc.result_id = result_key
          AND (
              cs.id IS NULL
              OR cr.id IS NULL
              OR cr.condition_id <> ec.id
              OR cr.decision <> 'approved'
              OR crs.id IS NULL
              OR ae.protocol_id <> res.protocol_id
              OR ae.condition_id <> ec.id
              OR ae.eligibility_status <> 'eligible'
              -- Condition review must be the current applicable review head for this condition
              OR cr.id <> (
                  SELECT r.id FROM public.review_event r
                  WHERE r.investigation_id = inv AND r.condition_id = ec.id
                  ORDER BY r.revision DESC LIMIT 1
              )
              OR NOT EXISTS (
                  SELECT 1 FROM public.approval_dependency d
                  WHERE d.investigation_id = inv AND d.owner_review_id = cr.id
                    AND d.entry_kind = 'decision' AND d.role = 'condition_content'
                    AND d.dependency_seal_id = cs.id
              )
              OR EXISTS (
                  SELECT 1 FROM public.condition_component k
                  WHERE k.investigation_id = inv AND k.condition_id = ec.id
                    AND NOT EXISTS (
                        SELECT 1 FROM public.approval_dependency d
                        JOIN public.review_event vr ON (vr.investigation_id, vr.id) = (inv, d.dependency_review_id)
                        JOIN public.aggregate_seal vs ON (vs.investigation_id, vs.review_id) = (inv, vr.id)
                        WHERE d.investigation_id = inv AND d.owner_review_id = cr.id
                          AND d.entry_kind = 'decision' AND d.role = 'variable_definition'
                          AND vr.variable_id = k.variable_id AND vr.decision = 'approved'
                          -- Variable review must be the current applicable review head for this variable
                          AND vr.id = (
                              SELECT r.id FROM public.review_event r
                              WHERE r.investigation_id = inv AND r.variable_id = k.variable_id
                              ORDER BY r.revision DESC LIMIT 1
                          )
                    )
              )
          );

        IF bad_cond_integrity > 0 THEN
            RETURN QUERY SELECT 'condition_approval_and_eligibility'::text, false, format('%s conditions fail seal/review/eligibility/approval lineage', bad_cond_integrity);
        ELSE
            RETURN QUERY SELECT 'condition_approval_and_eligibility'::text, true, 'All conditions have valid content seals, approved sealed reviews with variable lineage, and eligible status';
        END IF;

        -- Validate Active Input Policies
        SELECT count(*) INTO missing_active_components
        FROM public.result_input i
        JOIN public.semantic_annotation a ON (a.investigation_id, a.id) = (inv, i.annotation_id)
        JOIN public.scientific_variable v ON (v.investigation_id, v.id) = (inv, a.variable_id)
        JOIN public.condition_segment seg ON (seg.investigation_id, seg.id) = (inv, i.segment_id)
        JOIN public.protocol_requirement req ON (req.investigation_id, req.protocol_id, req.target_kind, req.requirement_key) =
                                                (inv, res.protocol_id, 'input', i.input_role)
        WHERE i.investigation_id = inv AND i.result_id = result_key
          AND (req.instrument_policy <> 'not_required' OR req.stability_policy <> 'not_applicable')
          AND NOT EXISTS (
              SELECT 1 FROM public.result_condition rc
              JOIN public.experimental_condition ec ON (ec.investigation_id, ec.id) = (inv, rc.condition_id)
              JOIN public.condition_component k ON (k.investigation_id, k.condition_id) = (inv, ec.id)
              JOIN public.condition_role r ON (r.investigation_id, r.id) = (inv, k.role_id)
              WHERE rc.investigation_id = inv AND rc.result_id = result_key
                AND ec.experimental_test_id = seg.experimental_test_id
                AND ec.segment_id = i.segment_id
                AND k.annotation_id = i.annotation_id
                AND k.variable_id = req.variable_id
                AND r.variable_category = v.variable_category
                AND (req.instrument_policy = 'not_required' OR (k.instrument_status = 'identified' AND k.instrument_id IS NOT NULL))
                AND (
                    req.stability_policy = 'not_applicable'
                    OR (req.stability_policy = 'transient_allowed' AND ec.airflow_stability IN ('stable', 'transient'))
                    OR (req.stability_policy = 'stable_required' AND ec.airflow_stability = 'stable')
                )
          );

        IF missing_active_components > 0 THEN
            RETURN QUERY SELECT 'active_input_policies'::text, false, format('%s inputs lack matching condition components for active policies', missing_active_components);
        ELSE
            RETURN QUERY SELECT 'active_input_policies'::text, true, 'Active input policies satisfied by matching condition components';
        END IF;

        -- Validate Condition-Role Requirements (when C > 0)
        IF c_count > 0 THEN
            SELECT count(*) INTO missing_condition_roles
            FROM (
                SELECT creq.id AS creq_id, seg.experimental_test_id, seg.segment_id, count(DISTINCT k.id) AS actual_count, creq.min_count, creq.max_count
                FROM public.protocol_requirement creq
                CROSS JOIN (
                    SELECT DISTINCT l.experimental_test_id, inp.segment_id
                    FROM public.result_input inp
                    JOIN public.test_source_record l ON (l.investigation_id, l.id) = (inv, inp.test_link_id)
                    WHERE inp.investigation_id = inv AND inp.result_id = result_key
                ) seg
                LEFT JOIN public.result_condition rc ON rc.investigation_id = inv AND rc.result_id = result_key
                LEFT JOIN public.experimental_condition ec ON (ec.investigation_id, ec.id) = (inv, rc.condition_id)
                                                          AND ec.experimental_test_id = seg.experimental_test_id
                                                          AND ec.segment_id = seg.segment_id
                LEFT JOIN public.condition_component k ON (k.investigation_id, k.condition_id) = (inv, ec.id)
                                                      AND k.role_id = creq.role_id
                                                      AND k.variable_id = creq.variable_id
                                                      AND (creq.instrument_policy = 'not_required' OR (k.instrument_status = 'identified' AND k.instrument_id IS NOT NULL))
                                                      AND (
                                                          creq.stability_policy = 'not_applicable'
                                                          OR (creq.stability_policy = 'transient_allowed' AND ec.airflow_stability IN ('stable', 'transient'))
                                                          OR (creq.stability_policy = 'stable_required' AND ec.airflow_stability = 'stable')
                                                      )
                WHERE creq.investigation_id = inv AND creq.protocol_id = res.protocol_id AND creq.target_kind = 'condition'
                GROUP BY creq.id, seg.experimental_test_id, seg.segment_id, creq.min_count, creq.max_count
            ) cr_match
            WHERE cr_match.actual_count < cr_match.min_count OR cr_match.actual_count > cr_match.max_count;

            IF missing_condition_roles > 0 THEN
                RETURN QUERY SELECT 'condition_role_requirements'::text, false, format('%s condition-role requirements not satisfied across input scopes', missing_condition_roles);
            ELSE
                RETURN QUERY SELECT 'condition_role_requirements'::text, true, 'All declared condition-role requirements satisfied with required counts';
            END IF;
        ELSE
            RETURN QUERY SELECT 'condition_role_requirements'::text, true, 'No condition-role requirements declared (C=0)';
        END IF;
    ELSE
        -- res_cond_count = 0
        IF c_count > 0 THEN
            RETURN QUERY SELECT 'condition_role_requirements'::text, false, 'Condition-role requirements declared but zero conditions present';
        ELSE
            RETURN QUERY SELECT 'condition_role_requirements'::text, true, 'No condition-role requirements declared (C=0)';
        END IF;
        IF NOT all_input_waived THEN
            RETURN QUERY SELECT 'active_input_policies'::text, false, 'Active input policies require conditions, but ResultCondition is empty';
        ELSE
            RETURN QUERY SELECT 'active_input_policies'::text, true, 'All input policies waived';
        END IF;
    END IF;
END $$;
-- next function
CREATE FUNCTION flare_n2.matches(inv uuid, result_key uuid) RETURNS boolean
LANGUAGE sql STABLE SET search_path = pg_catalog, public, pg_temp AS $$
    SELECT coalesce(bool_and(passed), false)
    FROM flare_n2.validate_result(inv, result_key);
$$;
-- next function
CREATE FUNCTION flare_n2.certify() RETURNS trigger
LANGUAGE plpgsql SET search_path = pg_catalog, public, pg_temp AS $$
DECLARE
    owner_key uuid;
    rev public.review_event;
BEGIN
    IF TG_TABLE_NAME = 'review_event' THEN
        owner_key := NEW.id;
    ELSE
        owner_key := NEW.review_id;
    END IF;

    IF owner_key IS NULL THEN
        RETURN NULL;
    END IF;

    SELECT * INTO rev FROM public.review_event
    WHERE investigation_id = NEW.investigation_id AND id = owner_key;

    IF rev.result_id IS NOT NULL AND rev.decision = 'approved' THEN
        IF NOT flare_n2.matches(NEW.investigation_id, rev.result_id) THEN
            RAISE EXCEPTION 'Final result review fails N2 condition-policy matching' USING ERRCODE = '23514';
        END IF;
    END IF;

    RETURN NULL;
END $$;
