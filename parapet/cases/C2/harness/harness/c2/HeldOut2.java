package harness.c2;

/** Held-out variant 2: a general external entity declared with a PUBLIC identifier. */
public final class HeldOut2 {
    private HeldOut2() {
    }

    public static void main(String[] args) {
        PayloadCheck.run("heldout2", files ->
                "<?xml version=\"1.0\"?>\n"
                + "<!DOCTYPE config [\n"
                + "  <!ENTITY leak PUBLIC \"-//PARAPET//CANARY//EN\" \"" + files.secretUri() + "\">\n"
                + "]>\n"
                + "<config><name>&leak;</name></config>\n");
    }
}
