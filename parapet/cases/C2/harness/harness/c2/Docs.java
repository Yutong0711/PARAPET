package harness.c2;

/** Deterministic legitimate configuration documents. */
final class Docs {
    private Docs() {
    }

    /** A ~7 KB configuration document with 30 servers, attributes, and comments. */
    static String workload() {
        StringBuilder b = new StringBuilder();
        b.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n");
        b.append("<config version=\"3\" tenant=\"acme-prod\">\n");
        b.append("  <!-- generated deployment configuration -->\n");
        b.append("  <cluster name=\"primary\" region=\"us-west-2\">\n");
        for (int i = 1; i <= 30; i++) {
            String id = String.format("server%02d", i);
            b.append("    <").append(id).append(" role=\"").append(i % 3 == 0 ? "db" : "web").append("\">\n");
            b.append("      <host>").append(id).append(".internal.example.org</host>\n");
            b.append("      <port>").append(8000 + i).append("</port>\n");
            b.append("      <tls enabled=\"true\" protocol=\"TLSv1.3\"/>\n");
            b.append("      <pool min=\"2\" max=\"").append(8 + i % 5).append("\">  pooled  </pool>\n");
            b.append("    </").append(id).append(">\n");
        }
        b.append("  </cluster>\n");
        b.append("  <logging level=\"info\"><path>/var/log/app/service.log</path></logging>\n");
        b.append("  <motd><![CDATA[Maintenance window: Sun 02:00-04:00 UTC & updates]]></motd>\n");
        b.append("</config>\n");
        return b.toString();
    }
}
