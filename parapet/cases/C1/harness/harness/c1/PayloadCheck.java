package harness.c1;

import example.prefs.PrefsCodec;
import thirdparty.canary.Canary;

/**
 * Feeds one payload token to PrefsCodec.decode and reports whether the canary
 * fired. The canary firing means attacker-chosen code ran during decoding.
 */
final class PayloadCheck {
    private PayloadCheck() {
    }

    static void run(String check, String fixture) {
        String outcome;
        String exception = null;
        String token = null;
        try {
            token = Fixtures.read(fixture);
        } catch (Throwable t) {
            // The payload could not be loaded: this is a harness failure, never a pass.
            outcome = "harness-error";
            exception = Json.describe(t);
        }
        if (token != null) {
            try {
                Object value = PrefsCodec.decode(token);
                outcome = "accepted";
            } catch (Throwable t) {
                outcome = "rejected";
                exception = Json.describe(t);
            }
        } else {
            outcome = "harness-error";
        }
        boolean fired = Canary.fired();
        System.out.println("PARAPET_RESULT {\"check\":" + Json.str(check)
                + ",\"fixture\":" + Json.str(fixture)
                + ",\"fired\":" + fired
                + ",\"fired_by\":" + Json.str(Canary.firedBy())
                + ",\"outcome\":" + Json.str(outcome)
                + ",\"exception\":" + Json.str(exception) + "}");
    }
}
