select
    count(sn.*)
from civil_service.staff_numbers sn
where
    sn.year = :year and
    sn.quarter = :quarter
