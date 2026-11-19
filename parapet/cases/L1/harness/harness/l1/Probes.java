package harness.l1;

import com.jamesmurty.utils.XMLBuilder;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;

/**
 * Legitimate documents the ORIGINAL library parses, including ones that use
 * DTD features. For each: whether XMLBuilder.parse(String) accepts it and a
 * digest of the serialized result.
 */
public final class Probes {
    interface Doc {
        String build(CanaryFiles files) throws Exception;
    }

    private Probes() {
    }

    static String digest(String s) throws Exception {
        byte[] h = MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8));
        StringBuilder hex = new StringBuilder();
        for (int i = 0; i < 8; i++) {
            hex.append(String.format("%02x", h[i]));
        }
        return hex.toString();
    }

    public static void main(String[] args) throws Exception {
        String[] names = {
            "typical_no_doctype",
            "comments_cdata_charrefs",
            "doctype_without_subset",
            "internal_entity",
            "internal_default_attribute",
            "external_dtd_benign_local",
        };
        Doc[] docs = {
            files -> Docs.workload(),
            files -> "<config><!-- c --><a><![CDATA[x<y]]></a><b>&amp;&#65;</b></config>",
            files -> "<!DOCTYPE config>\n<config><a>1</a></config>",
            files -> "<!DOCTYPE config [\n  <!ENTITY org \"Example Org\">\n]>\n<config><owner>&org;</owner></config>",
            files -> "<!DOCTYPE config [\n  <!ATTLIST server port CDATA \"8080\">\n]>\n<config><server host=\"a\"/></config>",
            files -> {
                String dtd = files.writeFile("benign.dtd", "<!ELEMENT config ANY>\n<!ELEMENT a (#PCDATA)>\n");
                return "<!DOCTYPE config SYSTEM \"" + dtd + "\">\n<config><a>1</a></config>";
            },
        };
        List<String> rows = new ArrayList<>();
        for (int i = 0; i < names.length; i++) {
            String status;
            String d = null;
            String exception = null;
            try (CanaryFiles files = new CanaryFiles()) {
                String xml = docs[i].build(files);
                try {
                    XMLBuilder b = XMLBuilder.parse(xml);
                    d = digest(b.getDocument().getDocumentElement().getTextContent() + "\u0000"
                            + b.getDocument().getElementsByTagName("*").getLength() + "\u0000"
                            + b.xpathQuery("count(//@*)", javax.xml.xpath.XPathConstants.NUMBER));
                    status = "accepted";
                } catch (Throwable t) {
                    status = "rejected";
                    exception = Json.describe(t);
                }
            }
            rows.add("{\"probe\":" + Json.str(names[i]) + ",\"status\":" + Json.str(status)
                    + ",\"digest\":" + Json.str(d) + ",\"exception\":" + Json.str(exception) + "}");
        }
        System.out.println("PARAPET_RESULT {\"check\":\"probes\",\"probes\":[" + String.join(",", rows) + "]}");
    }
}
