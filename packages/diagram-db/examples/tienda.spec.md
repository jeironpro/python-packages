# Esquema: Tienda

Spec de ejemplo para `diagram-db`. La prosa fuera de `## Entidades` se ignora,
así que este párrafo no afecta al diagrama.

## Entidades

### users
- id: int PK
- email: varchar(255) UK, not null
- name: varchar(120), not null
- manager_id: int FK -> users.id, null

### categories
- id: int PK
- name: varchar(80), not null
- parent_id: int FK -> categories.id, null

### products
- id: int PK
- category_id: int FK -> categories.id, not null
- sku: varchar(40) UK, not null
- name: varchar(200), not null
- price: decimal(10,2), not null

### orders
- id: int PK
- user_id: int FK -> users.id, not null
- placed_at: timestamptz, not null
- status: varchar(20), not null

### order_items
- order_id: int PK, FK -> orders.id
- product_id: int PK, FK -> products.id
- qty: int, not null
- unit_price: decimal(10,2), not null

### payments
- id: int PK
- order_id: int UK, FK -> orders.id, not null
- method: varchar(30), not null
- amount: decimal(10,2), not null

## Relaciones

- users.manager_id: 0..1:N "reporta a"
- payments.order_id: 1:1 "paga"

<!--
Relaciones que este spec debe producir:

users       1:N  orders        (orders.user_id, not null)
users       1:N  users         (users.manager_id, anulable, auto-relación, etiqueta "reporta a")
categories  1:N  categories    (categories.parent_id, anulable, auto-relación)
categories  1:N  products      (products.category_id, not null)
orders      1:N  order_items   (PK compuesta, tabla puente N:M con products)
products    1:N  order_items
orders      1:1  payments      (payments.order_id es UK, etiqueta "paga")
-->
