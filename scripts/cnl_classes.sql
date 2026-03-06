-- 中图分类SQL插入语句
-- 来源: 海纳中图分类.txt

BEGIN TRANSACTION;

-- 清空现有数据
DELETE FROM resource_class_map;
DELETE FROM resources;
DELETE FROM cnl_classes;

-- 插入分类数据
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A', '马克思主义、列宁主义、毛泽东思想、邓小平理论', NULL, 1, 'A');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A1', '马克思、恩格斯著作', (SELECT id FROM cnl_classes WHERE code = 'A'), 2, 'A/A1');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A11', '选集、文集', (SELECT id FROM cnl_classes WHERE code = 'A1'), 3, 'A/A1/A11');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A119', '选读', (SELECT id FROM cnl_classes WHERE code = 'A11'), 3, 'A/A1/A11/A119');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A12', '单行著作', (SELECT id FROM cnl_classes WHERE code = 'A1'), 3, 'A/A1/A12');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A13', '书信集、日记、函电、谈话', (SELECT id FROM cnl_classes WHERE code = 'A1'), 3, 'A/A1/A13');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A14', '诗词', (SELECT id FROM cnl_classes WHERE code = 'A1'), 3, 'A/A1/A14');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A15', '手迹', (SELECT id FROM cnl_classes WHERE code = 'A1'), 3, 'A/A1/A15');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A16', '专题汇编', (SELECT id FROM cnl_classes WHERE code = 'A1'), 3, 'A/A1/A16');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A18', '语录', (SELECT id FROM cnl_classes WHERE code = 'A1'), 3, 'A/A1/A18');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A2', '列宁著作', (SELECT id FROM cnl_classes WHERE code = 'A'), 2, 'A/A2');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A21', '选集、文集', (SELECT id FROM cnl_classes WHERE code = 'A2'), 3, 'A/A2/A21');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A219', '选读', (SELECT id FROM cnl_classes WHERE code = 'A21'), 3, 'A/A2/A21/A219');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A22', '单行著作', (SELECT id FROM cnl_classes WHERE code = 'A2'), 3, 'A/A2/A22');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A23', '书信集、日记、函电、谈话', (SELECT id FROM cnl_classes WHERE code = 'A2'), 3, 'A/A2/A23');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A25', '手迹', (SELECT id FROM cnl_classes WHERE code = 'A2'), 3, 'A/A2/A25');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A26', '专题汇编', (SELECT id FROM cnl_classes WHERE code = 'A2'), 3, 'A/A2/A26');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A28', '语录', (SELECT id FROM cnl_classes WHERE code = 'A2'), 3, 'A/A2/A28');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A3', '斯大林著作', (SELECT id FROM cnl_classes WHERE code = 'A'), 2, 'A/A3');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A31', '选集、文集', (SELECT id FROM cnl_classes WHERE code = 'A3'), 3, 'A/A3/A31');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A319', '选读', (SELECT id FROM cnl_classes WHERE code = 'A31'), 3, 'A/A3/A31/A319');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A32', '单行著作', (SELECT id FROM cnl_classes WHERE code = 'A3'), 3, 'A/A3/A32');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A33', '书信集、日记、函电、谈话', (SELECT id FROM cnl_classes WHERE code = 'A3'), 3, 'A/A3/A33');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A35', '手迹', (SELECT id FROM cnl_classes WHERE code = 'A3'), 3, 'A/A3/A35');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A36', '专题汇编', (SELECT id FROM cnl_classes WHERE code = 'A3'), 3, 'A/A3/A36');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A38', '语录', (SELECT id FROM cnl_classes WHERE code = 'A3'), 3, 'A/A3/A38');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A4', '毛泽东著作', (SELECT id FROM cnl_classes WHERE code = 'A'), 2, 'A/A4');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A41', '选集、文集', (SELECT id FROM cnl_classes WHERE code = 'A4'), 3, 'A/A4/A41');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A419', '选读', (SELECT id FROM cnl_classes WHERE code = 'A41'), 3, 'A/A4/A41/A419');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A42', '单行著作', (SELECT id FROM cnl_classes WHERE code = 'A4'), 3, 'A/A4/A42');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A43', '书信集、日记、函电、谈话', (SELECT id FROM cnl_classes WHERE code = 'A4'), 3, 'A/A4/A43');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A44', '诗词', (SELECT id FROM cnl_classes WHERE code = 'A4'), 3, 'A/A4/A44');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A45', '手迹', (SELECT id FROM cnl_classes WHERE code = 'A4'), 3, 'A/A4/A45');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A46', '专题汇编', (SELECT id FROM cnl_classes WHERE code = 'A4'), 3, 'A/A4/A46');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A48', '语录', (SELECT id FROM cnl_classes WHERE code = 'A4'), 3, 'A/A4/A48');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A49', '邓小平著作', (SELECT id FROM cnl_classes WHERE code = 'A4'), 3, 'A/A4/A49');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A5', '马克思、恩格斯、列宁、斯大林、毛泽东、邓小平著作汇编', (SELECT id FROM cnl_classes WHERE code = 'A'), 2, 'A/A5');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A56', '专题汇编', (SELECT id FROM cnl_classes WHERE code = 'A5'), 3, 'A/A5/A56');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A58', '语录', (SELECT id FROM cnl_classes WHERE code = 'A5'), 3, 'A/A5/A58');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A7', '马克思、恩格斯、列宁、斯大林、毛泽东、邓小平生平和传记', (SELECT id FROM cnl_classes WHERE code = 'A'), 2, 'A/A7');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A71', '马克思', (SELECT id FROM cnl_classes WHERE code = 'A7'), 3, 'A/A7/A71');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A72', '恩格斯', (SELECT id FROM cnl_classes WHERE code = 'A7'), 3, 'A/A7/A72');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A73', '列宁', (SELECT id FROM cnl_classes WHERE code = 'A7'), 3, 'A/A7/A73');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A74', '斯大林', (SELECT id FROM cnl_classes WHERE code = 'A7'), 3, 'A/A7/A74');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A75', '毛泽东', (SELECT id FROM cnl_classes WHERE code = 'A7'), 3, 'A/A7/A75');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A76', '邓小平', (SELECT id FROM cnl_classes WHERE code = 'A7'), 3, 'A/A7/A76');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A8', '马克思主义、列宁主义、毛泽东思想、邓小平理论的学习和研究', (SELECT id FROM cnl_classes WHERE code = 'A'), 2, 'A/A8');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A81', '马克思主义的学习和研究', (SELECT id FROM cnl_classes WHERE code = 'A8'), 3, 'A/A8/A81');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A82', '列宁主义的学习和研究', (SELECT id FROM cnl_classes WHERE code = 'A8'), 3, 'A/A8/A82');
INSERT INTO cnl_classes (code, name, parent_id, level, path) VALUES ('A83', '斯大林的思想的学习和研究', (SELECT id FROM cnl_classes WHERE code = 'A8'), 3, 'A/A8/A83');

COMMIT;
