package harness.l1;

import com.jamesmurty.utils.XMLBuilder;

/** Held-out variant 2: XMLBuilder.parse(String); a general external entity declared with a PUBLIC identifier. */
public final class HeldOut2 {
    private HeldOut2() {
    }

    public static void main(String[] args) {
        PayloadCheck.run("heldout2", "XMLBuilder.parse(String)", files ->
                "<?xml version=\"1.0\"?>\n"
                + "<!DOCTYPE config [\n"
                + "  <!ENTITY leak PUBLIC \"-//PARAPET//CANARY//EN\" \"" + files.secretUri() + "\">\n"
                + "]>\n"
                + "<config><name>&leak;</name></config>\n",
                xml -> {
                    XMLBuilder b = XMLBuilder.parse(xml);
                    return new String[] {b.asString(), b.getDocument().getDocumentElement().getTextContent()};
                });
    }
}
