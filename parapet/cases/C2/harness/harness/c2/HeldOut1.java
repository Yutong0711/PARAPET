package harness.c2;

/**
 * Held-out variant 1: no entity declaration in the document itself. The
 * DOCTYPE names an external DTD subset (a local file written by the check),
 * and that DTD declares the external entity.
 */
public final class HeldOut1 {
    private HeldOut1() {
    }

    public static void main(String[] args) {
        PayloadCheck.run("heldout1", files -> {
            String dtd = files.writeFile("ext.dtd",
                    "<!ENTITY leak SYSTEM \"" + files.secretUri() + "\">\n");
            return "<?xml version=\"1.0\"?>\n"
                    + "<!DOCTYPE config SYSTEM \"" + dtd + "\">\n"
                    + "<config><name>&leak;</name></config>\n";
        });
    }
}
