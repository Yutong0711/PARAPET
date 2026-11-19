package harness.l1;

import com.jamesmurty.utils.XMLBuilder;
import java.io.StringReader;
import org.xml.sax.InputSource;

/**
 * Held-out variant 1: XMLBuilder.parse(InputSource); no entity declaration in
 * the document itself -- the DOCTYPE names an external DTD subset (a local
 * file written by the check) that declares the external entity.
 */
public final class HeldOut1 {
    private HeldOut1() {
    }

    public static void main(String[] args) {
        PayloadCheck.run("heldout1", "XMLBuilder.parse(InputSource)", files -> {
            String dtd = files.writeFile("ext.dtd",
                    "<!ENTITY leak SYSTEM \"" + files.secretUri() + "\">\n");
            return "<?xml version=\"1.0\"?>\n"
                    + "<!DOCTYPE config SYSTEM \"" + dtd + "\">\n"
                    + "<config><name>&leak;</name></config>\n";
        }, xml -> {
            XMLBuilder b = XMLBuilder.parse(new InputSource(new StringReader(xml)));
            return new String[] {b.asString(), b.getDocument().getDocumentElement().getTextContent()};
        });
    }
}
