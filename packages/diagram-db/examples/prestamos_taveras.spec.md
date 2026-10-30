# Esquema: Préstamos Taveras

Sistema de préstamos semanales. Lo que está fuera de `## Entidades` no se
interpreta: sirve para documentar decisiones del modelo.

Convenciones:

- `uuid` es un hash SHA-256 en hexadecimal (64 caracteres) y actúa como clave
  pública de cada tabla; `id` es la clave primaria interna.
- `pagos.empleado_id` referencia a un usuario con rol EMPLEADO. El diagrama no
  puede expresar ese filtro: la columna guarda el id, no el rol.

## Entidades

### usuarios
- id: int PK
- uuid: char(64) UK, not null
- rol: enum(ADMIN, CLIENTE, EMPLEADO), not null
- nombre: varchar(100), not null
- apellidos: varchar(100), not null
- cedula: varchar(20) UK, not null
- correo: varchar(150) UK, not null
- contrasena: varchar(255), not null
- telefono: varchar(20)
- direccion: varchar(200)

### prestamos
- id: int PK
- uuid: char(64) UK, not null
- usuario_id: int FK -> usuarios.id, not null
- monto: decimal(12,2), not null
- monto_cuota: decimal(12,2), not null
- monto_mora: decimal(12,2), not null
- cantidad_semanas: int, not null
- dia_pago: enum(LUNES, MARTES, MIERCOLES, JUEVES, VIERNES, SABADO, DOMINGO), not null

### semanas_prestamo
- id: int PK
- uuid: char(64) UK, not null
- prestamo_id: int FK -> prestamos.id, not null
- numero_semana: int, not null
- monto: decimal(12,2), not null
- estado: enum(PAGADA, PENDIENTE, CANCELADA), not null
- fecha: date, not null

### pagos
- id: int PK
- uuid: char(64) UK, not null
- semanas_prestamo_id: int FK -> semanas_prestamo.id, not null
- monto: decimal(12,2), not null
- fecha: date, not null
- tipo: enum(CUOTA, MORA, AMBOS), not null
- metodo_pago: enum(EFECTIVO, TRANSFERENCIA), not null
- empleado_id: int FK -> usuarios.id, not null

### moras
- id: int PK
- uuid: char(64) UK, not null
- semanas_prestamo_id: int FK -> semanas_prestamo.id, not null
- monto: decimal(12,2), not null
- fecha: date, not null
- estado: enum(PAGADA, PENDIENTE, CANCELADA), not null
- metodo_pago: enum(EFECTIVO, TRANSFERENCIA)

## Relaciones

- prestamos.usuario_id: 1:N "solicita"
- semanas_prestamo.prestamo_id: 1:N "tiene"
- pagos.semanas_prestamo_id: 1:N "cubre"
- moras.semanas_prestamo_id: 1:N "genera"
- pagos.empleado_id: 1:N "registra"
