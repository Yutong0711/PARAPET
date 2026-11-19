package harness.c2;

import example.config.ConfigLoader;
import java.util.Map;

/** Loads one payload document and reports whether the canary marker leaked. */
final class PayloadCheck {
    interface Payload {
        String build(CanaryFiles files) throws Exception;
    }

    private PayloadCheck() {
    }

    static void run(String check, Payload payload) {
        String outcome;
        String exception = null;
        boolean fired = false;
        String where = null;
        try (CanaryFiles files = new CanaryFiles()) {
            String xml = payload.build(files);
            try {
                Map<String, String> result = ConfigLoader.load(xml);
                outcome = "accepted";
                for (Map.Entry<String, String> e : result.entrySet()) {
                    if (String.valueOf(e.getKey()).contains(CanaryFiles.MARKER)
                            || String.valueOf(e.getValue()).contains(CanaryFiles.MARKER)) {
                        fired = true;
                        where = "result:" + e.getKey();
                    }
                }
            } catch (Throwable t) {
                outcome = "rejected";
                exception = Json.describe(t);
                for (Throwable c = t; c != null; c = c.getCause()) {
                    if (String.valueOf(c.getMessage()).contains(CanaryFiles.MARKER)) {
                        fired = true;
                        where = "exception:" + c.getClass().getName();
                    }
                }
            }
        } catch (Throwable setup) {
            outcome = "harness-error";
            exception = Json.describe(setup);
        }
        System.out.println("PARAPET_RESULT {\"check\":" + Json.str(check)
                + ",\"fired\":" + fired
                + ",\"fired_by\":" + Json.str(where)
                + ",\"outcome\":" + Json.str(outcome)
                + ",\"exception\":" + Json.str(exception) + "}");
    }
}
