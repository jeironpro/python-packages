# Esquema: Biblioteca

Catálogo mínimo: quién escribe, qué se presta y quién lo recibe.

## Entidades

### autores
- id: int PK
- nombre: varchar(120), not null
- pais: varchar(60)

### libros
- id: int PK
- autor_id: int FK -> autores.id, not null
- titulo: varchar(200), not null
- isbn: varchar(20) UK, not null
- anio: int, not null

### socios
- id: int PK
- nombre: varchar(120), not null
- correo: varchar(150) UK, not null
- alta: date, not null

### prestamos
- id: int PK
- libro_id: int FK -> libros.id, not null
- socio_id: int FK -> socios.id, not null
- retirado: date, not null
- devuelto: date

## Relaciones

- libros.autor_id: 1:N "escribe"
- prestamos.libro_id: 1:N "presta"
- prestamos.socio_id: 1:N "recibe"
