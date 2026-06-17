-- Replicates the collated data for the civil service staff numbers data working file
-- NB: This turns all dates into 'periods', to facilitate temporal joins. These are defined as year * 4 + quarter, so e.g. 2020 Q4 becomes 2020 * 4 + 4 = 8084, with nulls set to 0 for start_period and the maximum integer that can be held in a SQL int column for end_period
-- NB: Temporal joins use _between_, which includes both endpoints, because start/end year/quarters in civil_service.organisation are inclusive and non-overlapping. I.e. if an organisation ends in period N, it's successor starts in period N + 1
-- NB: Join between `civil_service.organisation` and `civil_service.vw_organisation_departmental_group` needs to be a left join as organisation aggregations and disaggregations don't feature in `civil_service.vw_organisation_departmental_group`, by design
-- NB: `case` statements handle organisations that we're now classifying with type:
    -- 'Reporting total' ('Total employment'), as these are reported as having:
        -- ❌ Organisation type: Organisation name (Excel) vs 'Reporting total' (SQL)
        -- ❌ Departmental group short name: Organisation name (Excel) vs null (SQL), as we haven't set short names for things of type 'Reporting total'
        -- ✅ Latest organisation name: Organisation name (Excel) vs organisation name (SQL)*
        -- ❌ Latest departmental group short name: Organisation name (Excel) vs null (SQL), as we haven't set short names for things of type 'Reporting total'
    -- 'Security services' ('Central Government Security', 'Security and Intelligence Services'), as these are reported as having:
        -- ✅ Organisation type: 'Security services' (Excel) vs 'Security services' (SQL)
        -- ❌ Departmental group short name: 'Security services' (Excel) vs null (SQL), as we haven't set short names for things of type 'Reporting total'
        -- ✅ Latest organisation name: Latest organisation name (Excel) vs latest organisation name (SQL)*
        -- ❌ Latest departmental group short name: 'Security services' (Excel) vs null (SQL), as we haven't set short names for things of type 'Reporting total'
    -- *No case statement needed, as things match in both cases
-- NB: 'Organisation name' is renamed 'Organisation', so that existing PivotTable connections to collated datasets don't break
-- NB: 'IfG departmental group' is renamed 'Departmental group', so that existing PivotTable connections to collated datasets don't break
-- NB: 'Latest IfG departmental group' is renamed 'Latest departmental group', so that existing PivotTable connections to collated datasets don't break
with sn as (
    select
        *,
        sn.year * 4 + sn.quarter survey_period
    from civil_service.staff_numbers sn
),
o_vicd_vodg as (
    select
        o.id,
        vodg.organisation_name,
        o.type,
        vicd.is_ifg_core_department,
        vodg.ifg_departmental_group_id,
        vodg.ifg_departmental_group_name,
        vodg.ifg_departmental_group_short_name,
        vodg.start_year,
        vodg.start_quarter,
        vodg.end_year,
        vodg.end_quarter,
        isnull(vodg.start_year * 4 + vodg.start_quarter, 0) start_period,
        isnull(vodg.end_year * 4 + vodg.end_quarter, 2147483647) end_period
    from civil_service.organisation o
        left join civil_service.vw_ifg_core_departments vicd on
            o.id = vicd.organisation_id
        left join civil_service.vw_organisation_departmental_group vodg on
            o.id = vodg.organisation_id
)
select
    sn.id ID,
    sn.year Year,
    sn.quarter Quarter,
    sn.organisation_name Organisation,
    sn.headcount Headcount,
    sn.fte FTE,
    sn.original Original,
    case sn.organisation_name
        when 'Total employment' then 'Total employment'
        else o_vicd_vodg.type
    end [Organisation type],
    case sn.organisation_name
        when 'Total employment' then 'Total employment'
        when 'Security and Intelligence Services' then 'Security services'
        when 'Central Government Security' then 'Security services'
        else o_vicd_vodg.ifg_departmental_group_short_name
    end [Departmental group],
    iif(
        vol1.latest_organisation_name = 'Indeterminate',
        vol1.latest_determinate_organisation_name,
        vol1.latest_organisation_name
    ) [Latest organisation],
    case sn.organisation_name
        when 'Total employment' then 'Total employment'
        when 'Security and Intelligence Services' then 'Security services'
        when 'Central Government Security' then 'Security services'
        else iif(
            vol2.latest_organisation_name = 'Indeterminate',
            vol2.latest_determinate_organisation_short_name,
            vol2.latest_organisation_short_name
        )
    end [Latest departmental group]
from sn
    left join o_vicd_vodg on
        sn.organisation_id = o_vicd_vodg.id and
        sn.survey_period between o_vicd_vodg.start_period and o_vicd_vodg.end_period
    left join civil_service.vw_organisation_latest vol1 on
        o_vicd_vodg.id = vol1.organisation_id
    left join civil_service.vw_organisation_latest vol2 on
        o_vicd_vodg.ifg_departmental_group_id = vol2.organisation_id
order by
    sn.year,
    sn.quarter,
    sn.organisation_name
