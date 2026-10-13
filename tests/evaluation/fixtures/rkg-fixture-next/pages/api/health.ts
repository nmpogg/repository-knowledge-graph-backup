export default function health(req, res) {
  if (req.method === "GET") {
    res.status(200);
  }
}
