const fs = require("fs");

const file = "/app/frontend/src/config/enterpriseMenuConfig.js";
const txt = fs.readFileSync(file, "utf8");

const ids = [...txt.matchAll(/id:\s*"([^"]+)"/g)].map(x => x[1]);
const paths = [...txt.matchAll(/path:\s*"([^"]+)"/g)].map(x => x[1]);

const dupIds = ids.filter((x, i) => ids.indexOf(x) !== i);
const dupPaths = paths.filter((x, i) => paths.indexOf(x) !== i);

console.log("IDs totales:", ids.length);
console.log("Paths totales:", paths.length);

if (dupIds.length) {
  console.error("ERROR: IDs duplicados:", [...new Set(dupIds)]);
  process.exit(1);
}

const allowedDuplicatedPaths = [
  "/inteligencia-comercial"
];

const badDupPaths = [...new Set(dupPaths)].filter(p => {
  const count = paths.filter(x => x === p).length;
  return count > 1 && !allowedDuplicatedPaths.includes(p);
});

if (badDupPaths.length) {
  console.error("ERROR: Paths duplicados no permitidos:", badDupPaths);
  process.exit(1);
}

console.log("OK: Menú Enterprise válido.");
