INSERT INTO "product_category"(category_id, category_name)
VALUES
(1, 'Bier'),
(2, 'Alkoholfrei'),
(3, 'Wein');

INSERT INTO product(category_id, product_type, product_name)
VALUES
(2, 'beverage', 'Paulaner Spezi'),
(2, 'beverage', 'RedBull'),
(3, 'beverage', 'Berg Ulrichsbier');

INSERT INTO beverage(product_id, beverage_size)
VALUES
(1, 0.5),
(2, 0.25),
(3, 0.3);

INSERT INTO pricing(product_id, pricing_type, price)
VALUES
(1, 'normal', 1.5),
(1, 'party', 2.0),
(1, 'big_event', 3.0),

(2, 'normal', 2.5),
(2, 'party', 3.5),
(2, 'big_event', 4.0),

(3, 'normal', 2.0),
(3, 'party', 2.5),
(3, 'big_event', 3.5);
