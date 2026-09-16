-- Name change events effective from the new release quarter, used to recode restated rows for the previous quarter back to the pre-rename organisation name
select
    o1.name predecessor_name,
    o2.name successor_name
from civil_service.organisation_link ol
    inner join civil_service.organisation_link_event ole on
        ol.organisation_link_event_id = ole.id
    inner join civil_service.organisation o1 on
        ol.predecessor_organisation_id = o1.id
    inner join civil_service.organisation o2 on
        ol.successor_organisation_id = o2.id
where
    ol.type = 'Name change' and
    ole.year = :year and
    ole.quarter = :quarter
