package harness.c1;

/** Check "heldout1": decodes payload fixture heldout1.b64 and reports whether the canary fired. */
public final class HeldOut1 {
    private HeldOut1() {
    }

    public static void main(String[] args) {
        PayloadCheck.run("heldout1", "heldout1.b64");
    }
}
