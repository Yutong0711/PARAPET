package harness.c2;

import example.config.ConfigLoader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Functional tests: the behavior a fix must preserve, for configuration
 * documents without a DOCTYPE. Documents that use DTD features are NOT part
 * of the required behavior; how a patch treats them is reported by Probes.
 */
public final class FunctionalTests {
    interface Body {
        void run() throws Exception;
    }

    private static final List<String> RESULTS = new ArrayList<>();
    private static int passed;
    private static int failed;

    private FunctionalTests() {
    }

    static void test(String name, Body body) {
        String detail = null;
        boolean ok;
        try {
            body.run();
            ok = true;
        } catch (Throwable t) {
            ok = false;
            detail = Json.describe(t);
        }
        if (ok) {
            passed++;
        } else {
            failed++;
        }
        RESULTS.add("{\"name\":" + Json.str(name) + ",\"ok\":" + ok + ",\"detail\":" + Json.str(detail) + "}");
    }

    static void expect(Map<String, String> expected, String xml) throws Exception {
        Map<String, String> actual = ConfigLoader.load(xml);
        if (!expected.equals(actual)) {
            throw new AssertionError("expected " + expected + " but got " + actual);
        }
        if (!new ArrayList<>(expected.keySet()).equals(new ArrayList<>(actual.keySet()))) {
            throw new AssertionError("key order differs: " + actual.keySet());
        }
    }

    static Map<String, String> map(String... kv) {
        Map<String, String> m = new LinkedHashMap<>();
        for (int i = 0; i < kv.length; i += 2) {
            m.put(kv[i], kv[i + 1]);
        }
        return m;
    }

    public static void main(String[] args) {
        test("nested_elements", () -> expect(
                map("config.server.host", "example.org", "config.server.port", "8443", "config.mode", "prod"),
                "<config><server><host>example.org</host><port>8443</port></server><mode>prod</mode></config>"));
        test("attributes", () -> expect(
                map("config@v", "2", "config.db@pool", "8", "config.db@url", "jdbc:h2:mem", "config.db", ""),
                "<config v=\"2\"><db url=\"jdbc:h2:mem\" pool=\"8\"/></config>"));
        test("comments_ignored", () -> expect(
                map("config.a", "1"),
                "<config><!-- note --><a>1<!-- inner --></a></config>"));
        test("cdata_section", () -> expect(
                map("config.motd", "<b>hi</b> & bye"),
                "<config><motd><![CDATA[<b>hi</b> & bye]]></motd></config>"));
        test("predefined_and_char_refs", () -> expect(
                map("config.t", "& < > \" ' A B"),
                "<config><t>&amp; &lt; &gt; &quot; &apos; &#x41; &#66;</t></config>"));
        test("whitespace_trimmed", () -> expect(
                map("config.name", "svc one"),
                "<config>\n  <name>\n    svc one  \n  </name>\n</config>"));
        test("unicode_text", () -> expect(
                map("config.owner", "Zoë 王小明 🚀"),
                "<?xml version=\"1.0\" encoding=\"UTF-8\"?><config><owner>Zoë 王小明 🚀</owner></config>"));
        test("xml_declaration", () -> expect(
                map("config.a", "x"),
                "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>\n<config><a>x</a></config>"));
        test("document_order_preserved", () -> expect(
                map("config.z", "1", "config.a", "2", "config.m", "3"),
                "<config><z>1</z><a>2</a><m>3</m></config>"));
        test("workload_document", () -> {
            Map<String, String> m = ConfigLoader.load(Docs.workload());
            if (m.size() != 277) {
                throw new AssertionError("expected 277 keys, got " + m.size());
            }
            if (!"server07.internal.example.org".equals(m.get("config.cluster.server07.host"))) {
                throw new AssertionError("wrong host: " + m.get("config.cluster.server07.host"));
            }
            if (!"pooled".equals(m.get("config.cluster.server07.pool"))) {
                throw new AssertionError("wrong pool text");
            }
        });
        test("malformed_rejected_with_ioexception", () -> {
            try {
                ConfigLoader.load("<config><a></config>");
            } catch (IOException expected) {
                return;
            }
            throw new AssertionError("malformed document was not rejected with IOException");
        });
        System.out.println("PARAPET_RESULT {\"check\":\"functional\",\"passed\":" + passed
                + ",\"failed\":" + failed + ",\"tests\":[" + String.join(",", RESULTS) + "]}");
    }
}
