package harness.c1;

/** Minimal JSON string escaping for harness result lines. */
final class Json {
    private Json() {
    }

    static String str(String s) {
        if (s == null) {
            return "null";
        }
        StringBuilder b = new StringBuilder("\"");
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"': b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\r': b.append("\\r"); break;
                case '\t': b.append("\\t"); break;
                default:
                    if (c < 0x20) {
                        b.append(String.format("\\u%04x", (int) c));
                    } else {
                        b.append(c);
                    }
            }
        }
        return b.append('"').toString();
    }

    static String describe(Throwable t) {
        if (t == null) {
            return null;
        }
        String msg = t.getMessage();
        if (msg != null && msg.length() > 300) {
            msg = msg.substring(0, 300) + "...";
        }
        return t.getClass().getName() + (msg == null ? "" : ": " + msg);
    }
}
