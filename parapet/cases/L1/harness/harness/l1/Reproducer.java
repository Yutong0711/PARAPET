package harness.l1;

import com.jamesmurty.utils.XMLBuilder2;

/**
 * Check "reproducer" (the shape reported in upstream issue #6): XMLBuilder2.parse(String)
 * on a document whose internal DTD subset declares a SYSTEM external entity
 * pointing at the canary file.
 */
public final class Reproducer {
    private Reproducer() {
    }

    public static void main(String[] args) {
        PayloadCheck.run("reproducer", "XMLBuilder2.parse(String)", files ->
                "<?xml version=\"1.0\"?>\n"
                + "<!DOCTYPE config [\n"
                + "  <!ENTITY xxe SYSTEM \"" + files.secretUri() + "\">\n"
                + "]>\n"
                + "<config><name>&xxe;</name></config>\n",
                xml -> {
                    XMLBuilder2 b = XMLBuilder2.parse(xml);
                    return new String[] {b.asString(), b.getDocument().getDocumentElement().getTextContent()};
                });
    }
}
