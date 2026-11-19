package harness.c1;

import example.prefs.PrefsCodec;
import example.prefs.PrefsCodec.UserPrefs;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;

/**
 * Legitimate tokens written by the ORIGINAL implementation (see MakeFixtures).
 * For each one, reports whether decode accepts it and a digest of the decoded
 * value, so a patch can be compared with the original: which inputs it now
 * rejects, and which it accepts with a different result.
 */
public final class Probes {
    static final String[] PROBES = {
        "probe_typical.b64",
        "probe_empty.b64",
        "probe_large.b64",
        "probe_unicode.b64",
        "probe_legacy_linkedlist.b64",
        "probe_legacy_hashmap.b64",
    };

    private Probes() {
    }

    public static void main(String[] args) throws Exception {
        List<String> rows = new ArrayList<>();
        for (String name : PROBES) {
            String status;
            String digest = null;
            String exception = null;
            String token;
            try {
                token = Fixtures.read(name);
            } catch (Throwable t) {
                rows.add("{\"probe\":" + Json.str(name) + ",\"status\":\"harness-error\",\"digest\":null,"
                        + "\"exception\":" + Json.str(Json.describe(t)) + "}");
                continue;
            }
            try {
                UserPrefs p = PrefsCodec.decode(token);
                MessageDigest md = MessageDigest.getInstance("SHA-256");
                byte[] h = md.digest(Samples.canonical(p).getBytes(StandardCharsets.UTF_8));
                StringBuilder hex = new StringBuilder();
                for (int i = 0; i < 8; i++) {
                    hex.append(String.format("%02x", h[i]));
                }
                digest = hex.toString();
                status = "accepted";
            } catch (Throwable t) {
                status = "rejected";
                exception = Json.describe(t);
            }
            rows.add("{\"probe\":" + Json.str(name) + ",\"status\":" + Json.str(status)
                    + ",\"digest\":" + Json.str(digest) + ",\"exception\":" + Json.str(exception) + "}");
        }
        System.out.println("PARAPET_RESULT {\"check\":\"probes\",\"probes\":[" + String.join(",", rows) + "]}");
    }
}
