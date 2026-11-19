package harness.c1;

/** Check "heldout2": decodes payload fixture heldout2.b64 and reports whether the canary fired. */
public final class HeldOut2 {
    private HeldOut2() {
    }

    public static void main(String[] args) {
        PayloadCheck.run("heldout2", "heldout2.b64");
    }
}
