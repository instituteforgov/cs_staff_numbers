-- Augments source data with IfG-derived organisation attributes
-- See README for an explanation of differences between the compare_data.sql script and this one
-- NB: Where data exists in both 'Original' and 'Restated' form for the same organisation and quarter, the 'Restated' row is preferred
-- NB: 'IfG core department' is recoded to 'Y'/'N' to make it more user-friendly
-- NB: 'Organisation name' is renamed 'Organisation', so that existing PivotTable connections to collated datasets don't break
-- NB: 'IfG departmental group' is renamed 'Latest departmental group', so that existing PivotTable connections to collated datasets don't break
-- NB: 'Latest IfG departmental group' is renamed 'Latest departmental group', so that existing PivotTable connections to collated datasets don't break
with sn as (
    select
        *,
        sn.year * 4 + sn.quarter survey_period,
        row_number() over (
            partition by sn.organisation_id, sn.year, sn.quarter
            order by case when sn.original = 'Restated' then 0 else 1 end
        ) rn
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
    sn.id,
    sn.year Year,
    sn.quarter Quarter,
    sn.organisation_name Organisation,
    o_vicd_vodg.type [Organisation type],
    case sn.organisation_name
        when 'Total employment' then 'Total employment'
        when 'Security and Intelligence Services' then 'Security services'
        when 'Central Government Security' then 'Security services'
        else o_vicd_vodg.ifg_departmental_group_short_name
    end [Departmental group],
    iif(o_vicd_vodg.is_ifg_core_department = 1, 'Y', 'N') [IfG core department],
    vol1.latest_organisation_name [Latest organisation],
    case sn.organisation_name
        when 'Total employment' then 'Total employment'
        when 'Security and Intelligence Services' then 'Security services'
        when 'Central Government Security' then 'Security services'
        else vol2.latest_organisation_short_name
    end [Latest departmental group],
    sn.original Original,
    sn.headcount Headcount,
    sn.fte FTE,
    sn.rn
from sn
    left join o_vicd_vodg on
        sn.organisation_id = o_vicd_vodg.id and
        sn.survey_period between o_vicd_vodg.start_period and o_vicd_vodg.end_period
    left join civil_service.vw_organisation_latest vol1 on
        o_vicd_vodg.id = vol1.organisation_id
    left join civil_service.vw_organisation_latest vol2 on
        o_vicd_vodg.ifg_departmental_group_id = vol2.organisation_id
where
    sn.rn = 1
order by
    sn.year,
    sn.quarter,
    sn.organisation_name
