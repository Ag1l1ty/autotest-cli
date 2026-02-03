const express = require("express");

const app = express();
app.use(express.json());

const items = [];

app.get("/health", (_req, res) => {
  res.json({ status: "ok" });
});

app.get("/items", (_req, res) => {
  res.json(items);
});

app.post("/items", (req, res) => {
  const { name } = req.body;
  if (\!name) {
    return res.status(400).json({ error: "Name is required" });
  }
  const item = { id: items.length + 1, name };
  items.push(item);
  res.status(201).json(item);
});

const PORT = process.env.PORT || 3000;
if (require.main === module) {
  app.listen(PORT, () => {
    console.log("Server running on port " + PORT);
  });
}

module.exports = app;
