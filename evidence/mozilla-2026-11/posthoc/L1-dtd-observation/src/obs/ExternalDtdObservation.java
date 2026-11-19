package obs;

import com.jamesmurty.utils.XMLBuilder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * T3 supplementary observation (not a check, not part of any claim level).
 * The document's DOCTYPE names a local DTD file (written here, in a fresh
 * temporary directory) that declares an INTERNAL entity holding a marker
 * string; the body uses the entity. If the marker appears in the parsed
 * document, the parser read the external DTD named by the document.
 */
public final class ExternalDtdObservation {
    static final String MARKER = "PARAPET-DTD-LOADED-3f8a";

    private ExternalDtdObservation() {
    }

    static String esc(String s) {
        return s == null ? "null" : "\"" + s.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\"";
    }

    public static void main(String[] args) throws Exception {
        Path dir = Files.createTempDirectory("parapet-l1obs-");
        Path dtd = dir.resolve("internal-entity.dtd");
        Files.write(dtd, ("<!ENTITY note \"" + MARKER + "\">\n").getBytes(StandardCharsets.US_ASCII));
        String xml = "<?xml version=\"1.0\"?>\n"
                + "<!DOCTYPE config SYSTEM \"" + dtd.toUri() + "\">\n"
                + "<config><name>&note;</name></config>\n";
        String status;
        String detail;
        try {
            XMLBuilder b = XMLBuilder.parse(xml);
            String text = b.getDocument().getDocumentElement().getTextContent();
            String serialized = b.asString();
            boolean loaded = text.contains(MARKER) || serialized.contains(MARKER);
            status = loaded ? "DTD loaded (marker present)" : "not loaded (accepted, marker absent)";
            detail = "text content: " + text + " | serialized: " + serialized;
        } catch (Throwable t) {
            status = "document rejected";
            detail = t.getClass().getName() + ": " + t.getMessage();
        } finally {
            Files.deleteIfExists(dtd);
            Files.deleteIfExists(dir);
        }
        System.out.println("PARAPET_OBS {\"status\":" + esc(status) + ",\"detail\":" + esc(detail) + "}");
    }
}
