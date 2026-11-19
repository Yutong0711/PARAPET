package harness.c2;

import example.config.ConfigLoader;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Legitimate documents the ORIGINAL loader accepts, including ones that use
 * DTD features. For each, reports whether load() accepts it and a digest of
 * the result, so a patch can be compared with the original.
 */
public final class Probes {
    interface Doc {
        String build(CanaryFiles files) throws Exception;
    }

    private Probes() {
    }

    static String digest(Map<String, String> m) throws Exception {
        StringBuilder b = new StringBuilder();
        for (Map.Entry<String, String> e : m.entrySet()) {
            b.append(e.getKey()).append('=').append(e.getValue()).append('\u0001');
        }
        byte[] h = MessageDigest.getInstance("SHA-256").digest(b.toString().getBytes(StandardCharsets.UTF_8));
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
                    d = digest(ConfigLoader.load(xml));
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
