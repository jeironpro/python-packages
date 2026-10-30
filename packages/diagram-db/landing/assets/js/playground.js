/* diagram-db — landing/playground.js
   Ejecuta el analizador auténtico (src/diagram_db) en el navegador con Pyodide.
   Python se descarga solo cuando el usuario pide el primer análisis y el
   paquete se carga desde ./vendor/diagram_db, sincronizado en CI. */
(() => {
  "use strict";

  const $ = (selector, scope = document) => scope.querySelector(selector);
  const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];

  const input = $("#spec-input");
  const runBtn = $("#pg-run");
  const status = $("#pg-status");
  const idle = $("#pg-idle");
  const list = $("#pg-diagnostics");
  const dotBox = $("#pg-dot-box");
  const dotOut = $("#pg-dot");
  const errorBox = $("#pg-error");
  const errorMsg = $("#pg-error-msg");

  if (!input || !runBtn) return;

  /* ============ Ejemplos ============ */

  const EXAMPLES = {
    tienda: `# Esquema: Tienda

## Entidades

### users
- id: int PK
- email: varchar(255) UK, not null
- manager_id: int FK -> users.id, null

### products
- id: int PK
- sku: varchar(40) UK, not null
- price: decimal(10,2), not null

### orders
- id: int PK
- user_id: int FK -> users.id, not null
- placed_at: timestamptz, not null

### order_items
- order_id: int PK, FK -> orders.id
- product_id: int PK, FK -> products.id
- qty: int, not null

## Relaciones

- users.manager_id: 0..1:N "reporta a"`,

    biblioteca: `# Esquema: Biblioteca

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

### prestamos
- id: int PK
- libro_id: int FK -> libros.id, not null
- retirado: date, not null
- devuelto: date

## Relaciones

- libros.autor_id: 1:N "escribe"
- prestamos.libro_id: 1:N "presta"`,

    roto: `# Esquema: Ventas

## Entidades

### clientes
- id: int PK
- nombre: varchar(120), not null

### pedidos
- id: int PK
- cliente_id: int FK -> clientes.id, not null
- total: decimal(10,2), not null

### detalle
- pedido_id: int FK -> pedidos.id
- producto_id: int FK -> productos.id
- cantidad: int, not null

### envios
- id: int PK
- pedido_id: varchar(20) FK -> pedidos.id, not null`,
  };

  const setExample = (name) => {
    if (!EXAMPLES[name]) return;
    input.value = EXAMPLES[name];
    reset();
  };

  const chips = $$(".chip[data-example]");
  chips.forEach((chip) => {
    chip.addEventListener("click", () => {
      chips.forEach((item) => {
        const active = item === chip;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-pressed", String(active));
      });
      setExample(chip.dataset.example);
    });
  });

  const reset = () => {
    status.textContent = "";
    idle.hidden = false;
    list.hidden = true;
    list.innerHTML = "";
    dotBox.hidden = true;
    dotBox.open = false;
    dotOut.textContent = "";
    errorBox.hidden = true;
    errorMsg.textContent = "";
  };

  setExample("tienda");

  /* ============ Motor: Pyodide + paquete real ============ */

  const PYODIDE_VERSION = "0.27.2";
  const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/pyodide.js`;
  const PYODIDE_INDEX = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;

  // Los mismos módulos que instala pip, servidos desde ./vendor (ver CI).
  const MODULES = [
    "__init__.py",
    "cardinality.py",
    "diagnostics.py",
    "model.py",
    "parser.py",
    "render.py",
    "validate.py",
  ];
  const PACKAGE_DIR = "/site/diagram_db";

  let pyodide = null;
  let notebook = null;

  const loadPyodideScript = () =>
    new Promise((resolve, reject) => {
      if (window.loadPyodide) return resolve();
      const script = document.createElement("script");
      script.src = PYODIDE_URL;
      script.onload = resolve;
      script.onerror = () =>
        reject(new Error("No se pudo descargar Pyodide desde el CDN"));
      document.head.appendChild(script);
    });

  const RUNNER = `
import json

from diagram_db import SpecError, build_relations, parse_spec, to_dot, validate


def _item(diagnostico):
    return {
        "code": diagnostico.code,
        "text": diagnostico.format("spec.md"),
        "error": diagnostico.is_error,
    }


def analizar(src):
    try:
        schema = parse_spec(src)
    except SpecError as exc:
        return json.dumps(
            {"ok": False, "diagnostics": [_item(d) for d in exc.diagnostics]}
        )
    schema, diagnostics = validate(schema)
    items = [_item(d) for d in (*schema.warnings, *diagnostics)]
    if any(item["error"] for item in items):
        return json.dumps({"ok": False, "diagnostics": items})
    relations = build_relations(schema)
    return json.dumps(
        {
            "ok": True,
            "diagnostics": items,
            "dot": to_dot(schema, relations),
            "entities": len(schema.entities),
            "relations": len(relations),
        }
    )
`;

  const ensureEngine = async () => {
    if (notebook) return notebook;

    status.textContent = "Descargando Python (WebAssembly)… ~10 MB, solo una vez";
    await loadPyodideScript();
    pyodide = await window.loadPyodide({ indexURL: PYODIDE_INDEX });

    status.textContent = "Cargando el analizador…";
    pyodide.FS.mkdirTree(PACKAGE_DIR);
    for (const name of MODULES) {
      const response = await fetch(`./vendor/diagram_db/${name}`);
      if (!response.ok) {
        throw new Error(`No se pudo cargar diagram_db/${name} (${response.status})`);
      }
      pyodide.FS.writeFile(`${PACKAGE_DIR}/${name}`, await response.text());
    }

    pyodide.runPython(
      `import sys; sys.path.insert(0, "/site"); import diagram_db`,
    );
    pyodide.runPython(RUNNER);
    notebook = pyodide;
    return notebook;
  };

  const analyze = (source) => {
    pyodide.globals.set("__spec_src", source);
    const raw = pyodide.runPython("analizar(__spec_src)");
    return JSON.parse(String(raw));
  };

  /* ============ Salida ============ */

  const renderDiagnostics = (items) => {
    list.innerHTML = "";
    items.forEach((item) => {
      const row = document.createElement("li");
      row.dataset.severity = item.error ? "error" : "warning";
      row.textContent = item.text;
      list.appendChild(row);
    });
    list.hidden = items.length === 0;
  };

  runBtn.addEventListener("click", async () => {
    runBtn.disabled = true;
    idle.hidden = true;
    list.hidden = true;
    dotBox.hidden = true;
    errorBox.hidden = true;

    try {
      await ensureEngine();
      const result = analyze(input.value);
      renderDiagnostics(result.diagnostics || []);

      if (result.ok) {
        const total = result.diagnostics.length;
        status.textContent = `${result.entities} entidades · ${result.relations} aristas${
          total ? ` · ${total} aviso${total === 1 ? "" : "s"}` : ""
        }`;
        dotOut.textContent = result.dot;
        dotBox.hidden = false;
      } else {
        const errors = result.diagnostics.filter((item) => item.error).length;
        status.textContent = `${errors} error${errors === 1 ? "" : "es"} · sin diagrama`;
      }
    } catch (error) {
      status.textContent = "";
      errorMsg.textContent = /Pyodide|vendor/.test(error.message)
        ? `${error.message}. Revisa la conexión o recarga la página.`
        : `Fallo inesperado: ${error.message}`;
      errorBox.hidden = false;
    } finally {
      runBtn.disabled = false;
    }
  });
})();
