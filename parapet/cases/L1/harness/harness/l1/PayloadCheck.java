package harness.l1;

/**
 * Parses one payload document through the library's public API and reports
 * whether the canary marker leaked into the parsed document (its serialized
 * form or its text content) or into an error message.
 */
final class PayloadCheck {
    interface Payload {
        String build(CanaryFiles files) throws Exception;
    }

    interface Parser {
        String[] parse(String xml) throws Exception;   // returns observable outputs
    }

    private PayloadCheck() {
    }

    static void run(String check, String api, Payload payload, Parser parser) {
        String outcome;
        String exception = null;
        boolean fired = false;
        String where = null;
        try (CanaryFiles files = new CanaryFiles()) {
            String xml = payload.build(files);
            try {
                String[] outputs = parser.parse(xml);
                outcome = "accepted";
                for (String o : outputs) {
                    if (o != null && o.contains(CanaryFiles.MARKER)) {
                        fired = true;
                        where = "parsed document";
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
                + ",\"api\":" + Json.str(api)
                + ",\"fired\":" + fired
                + ",\"fired_by\":" + Json.str(where)
                + ",\"outcome\":" + Json.str(outcome)
                + ",\"exception\":" + Json.str(exception) + "}");
    }
}
