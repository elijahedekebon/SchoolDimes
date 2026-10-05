"""Server-side CSV (RFC 4180 quoting) -- replaces lib/csv.ts, same columns."""
import csv
import io
import json

from django.http import HttpResponse


def csv_response(filename, rows, columns=None):
    cols = columns or list(dict.fromkeys(k for r in rows for k in r))
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(cols)
    for r in rows:
        writer.writerow(["" if r.get(c) is None else json.dumps(r[c]) if isinstance(r.get(c), (dict, list))
                         else str(r[c]).lower() if isinstance(r.get(c), bool) else r[c] for c in cols])
    response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
