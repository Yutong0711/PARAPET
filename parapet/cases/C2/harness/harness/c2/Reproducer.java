package harness.c2;

/** Check "reproducer": an internal-subset general external entity (SYSTEM) pointing at the canary file. */
public final class Reproducer {
    private Reproducer() {
    }

    public static void main(String[] args) {
        PayloadCheck.run("reproducer", files ->
                "<?xml version=\"1.0\"?>\n"
                + "<!DOCTYPE config [\n"
                + "  <!ENTITY xxe SYSTEM \"" + files.secretUri() + "\">\n"
                + "]>\n"
                + "<config><name>&xxe;</name></config>\n");
    }
}
