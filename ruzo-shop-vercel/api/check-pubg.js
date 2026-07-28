// Vercel serverless function
// GET /api/check-pubg?id=5930748140
// Returns: { ok: true, nickname: "..." } or { ok: false, error: "..." }
//
// Requires environment variable RAPIDAPI_KEY to be set in your Vercel project
// (Project Settings -> Environment Variables -> RAPIDAPI_KEY).

module.exports = async function handler(req, res) {
  const id = (req.query.id || '').toString().trim();

  if (id.length < 4) {
    return res.status(400).json({ ok: false, error: 'ID juda qisqa' });
  }

  const RAPIDAPI_KEY = process.env.RAPIDAPI_KEY;
  const RAPIDAPI_HOST = 'check-id-game.p.rapidapi.com';

  if (!RAPIDAPI_KEY) {
    return res.status(500).json({ ok: false, error: 'RAPIDAPI_KEY sozlanmagan (Vercel Environment Variables)' });
  }

  try {
    const apiRes = await fetch(
      `https://${RAPIDAPI_HOST}/api/rapid_api/cekpubgmobile/${encodeURIComponent(id)}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'x-rapidapi-host': RAPIDAPI_HOST,
          'x-rapidapi-key': RAPIDAPI_KEY,
        },
      }
    );

    const data = await apiRes.json();

    // Response shape can vary slightly by plan, so check a few likely fields.
    const nickname =
      data.nickname ||
      data.username ||
      (data.data && (data.data.nickname || data.data.username));

    if (apiRes.ok && nickname) {
      return res.status(200).json({ ok: true, nickname });
    }

    return res.status(200).json({ ok: false, error: data.error || 'ID topilmadi' });
  } catch (err) {
    return res.status(500).json({ ok: false, error: 'Server xatoligi' });
  }
};
