-- SQL to update Supabase remotely
-- Run this in the Supabase SQL Editor

ALTER TABLE departments ADD COLUMN IF NOT EXISTS link TEXT;

-- Update Links
UPDATE departments SET link = 'https://kbs.kfupm.edu.sa/academics/accounting-and-finance/' WHERE id = 1;
UPDATE departments SET link = 'https://kbs.kfupm.edu.sa/academics/accounting-and-finance/' WHERE id = 2;
UPDATE departments SET link = 'https://kbs.kfupm.edu.sa/academics/management-marketing/' WHERE id = 3;
UPDATE departments SET link = 'https://kbs.kfupm.edu.sa/academics/information-systems-and-operations-management/' WHERE id = 4;
UPDATE departments SET link = 'https://kbs.kfupm.edu.sa/academics/management-marketing/' WHERE id = 5;
UPDATE departments SET link = 'https://aecm.kfupm.edu.sa/' WHERE id = 6;
UPDATE departments SET link = 'https://acd.kfupm.edu.sa/' WHERE id = 7;
UPDATE departments SET link = 'https://ce.kfupm.edu.sa/' WHERE id = 8;
UPDATE departments SET link = 'https://ce.kfupm.edu.sa/' WHERE id = 9;
UPDATE departments SET link = 'https://itd.kfupm.edu.sa/' WHERE id = 10;
UPDATE departments SET link = 'https://cpg.kfupm.edu.sa/academics/departments/department-of-geosciences/' WHERE id = 12;
UPDATE departments SET link = 'https://cpg.kfupm.edu.sa/academics/departments/department-of-petroleum-engineering/' WHERE id = 15;
UPDATE departments SET link = 'https://ee.kfupm.edu.sa/' WHERE id = 16;
UPDATE departments SET link = 'https://ae.kfupm.edu.sa/' WHERE id = 17;
UPDATE departments SET link = 'https://cie.kfupm.edu.sa/' WHERE id = 18;
UPDATE departments SET link = 'https://kbs.kfupm.edu.sa/academics/management-marketing/' WHERE id = 19;
UPDATE departments SET link = 'https://ise.kfupm.edu.sa/' WHERE id = 20;
UPDATE departments SET link = 'https://math.kfupm.edu.sa/' WHERE id = 21;
UPDATE departments SET link = 'https://coe.kfupm.edu.sa/' WHERE id = 24;
UPDATE departments SET link = 'https://ics.kfupm.edu.sa/' WHERE id = 25;
UPDATE departments SET link = 'https://bioe.kfupm.edu.sa/' WHERE id = 26;
UPDATE departments SET link = 'https://che.kfupm.edu.sa/' WHERE id = 27;
UPDATE departments SET link = 'https://chemistry.kfupm.edu.sa/' WHERE id = 28;
UPDATE departments SET link = 'https://mse.kfupm.edu.sa/' WHERE id = 29;
UPDATE departments SET link = 'https://me.kfupm.edu.sa/' WHERE id = 30;
UPDATE departments SET link = 'https://physics.kfupm.edu.sa/' WHERE id = 31;
UPDATE departments SET link = 'https://eld.kfupm.edu.sa/' WHERE id = 34;
UPDATE departments SET link = 'https://kbs.kfupm.edu.sa/academics/global-studies/' WHERE id = 35;
UPDATE departments SET link = 'https://ias.kfupm.edu.sa/' WHERE id = 38;
UPDATE departments SET link = 'https://kbs.kfupm.edu.sa/academics/information-systems-and-operations-management/' WHERE id = 39;
UPDATE departments SET link = 'https://pe.kfupm.edu.sa/' WHERE id = 40;
UPDATE departments SET link = 'https://aecm.kfupm.edu.sa/' WHERE id = 46;
UPDATE departments SET link = 'https://ics.kfupm.edu.sa/' WHERE id = 49;
