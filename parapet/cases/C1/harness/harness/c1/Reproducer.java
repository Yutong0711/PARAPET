package harness.c1;

/** Check "reproducer": decodes payload fixture reproducer.b64 and reports whether the canary fired. */
public final class Reproducer {
    private Reproducer() {
    }

    public static void main(String[] args) {
        PayloadCheck.run("reproducer", "reproducer.b64");
    }
}
