package example.prefs;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.EOFException;
import java.io.IOException;
import java.io.Serializable;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Saves and restores a user's editor preferences as a compact text token.
 *
 * The token is stored in a browser cookie and sent back with later requests,
 * where {@link #decode(String)} turns it back into preferences.
 */
public final class PrefsCodec {

    /*
     * Tokens use an explicit data-only format instead of Java object
     * serialization: decode() reads strings and integers field by field and
     * never instantiates a class named by the input. Format (big-endian):
     * magic, version, user, theme, fontSize, recentFiles, shortcuts, where a
     * string is a length (-1 for null) followed by UTF-8 bytes and a list or
     * map is a count followed by its strings.
     */
    private static final int MAGIC = 0x50524546; // "PREF"
    private static final int VERSION = 1;
    private static final int MAX_ENTRIES = 100_000;

    private PrefsCodec() {
    }

    /** A user's editor preferences. */
    public static final class UserPrefs implements Serializable {
        private static final long serialVersionUID = 1L;

        private final String user;
        private final String theme;
        private final int fontSize;
        private final List<String> recentFiles;
        private final Map<String, String> shortcuts;

        public UserPrefs(String user, String theme, int fontSize,
                         List<String> recentFiles, Map<String, String> shortcuts) {
            this.user = user;
            this.theme = theme;
            this.fontSize = fontSize;
            this.recentFiles = new ArrayList<>(recentFiles);
            this.shortcuts = new LinkedHashMap<>(shortcuts);
        }

        public String getUser() {
            return user;
        }

        public String getTheme() {
            return theme;
        }

        public int getFontSize() {
            return fontSize;
        }

        public List<String> getRecentFiles() {
            return Collections.unmodifiableList(recentFiles);
        }

        public Map<String, String> getShortcuts() {
            return Collections.unmodifiableMap(shortcuts);
        }

        @Override
        public boolean equals(Object o) {
            if (this == o) {
                return true;
            }
            if (!(o instanceof UserPrefs)) {
                return false;
            }
            UserPrefs other = (UserPrefs) o;
            return fontSize == other.fontSize
                    && Objects.equals(user, other.user)
                    && Objects.equals(theme, other.theme)
                    && Objects.equals(recentFiles, other.recentFiles)
                    && Objects.equals(shortcuts, other.shortcuts);
        }

        @Override
        public int hashCode() {
            return Objects.hash(user, theme, fontSize, recentFiles, shortcuts);
        }

        @Override
        public String toString() {
            return "UserPrefs{user=" + user + ", theme=" + theme + ", fontSize=" + fontSize
                    + ", recentFiles=" + recentFiles + ", shortcuts=" + shortcuts + "}";
        }
    }

    /** Turns preferences into a Base64 token. */
    public static String encode(UserPrefs prefs) throws IOException {
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        try (DataOutputStream out = new DataOutputStream(bytes)) {
            out.writeInt(MAGIC);
            out.writeByte(VERSION);
            writeString(out, prefs.user);
            writeString(out, prefs.theme);
            out.writeInt(prefs.fontSize);
            out.writeInt(prefs.recentFiles.size());
            for (String file : prefs.recentFiles) {
                writeString(out, file);
            }
            out.writeInt(prefs.shortcuts.size());
            for (Map.Entry<String, String> e : prefs.shortcuts.entrySet()) {
                writeString(out, e.getKey());
                writeString(out, e.getValue());
            }
        }
        return Base64.getEncoder().encodeToString(bytes.toByteArray());
    }

    /** Restores preferences from a token produced by {@link #encode(UserPrefs)}. */
    public static UserPrefs decode(String token) throws IOException {
        byte[] data = Base64.getDecoder().decode(token);
        DataInputStream in = new DataInputStream(new ByteArrayInputStream(data));
        try {
            if (in.readInt() != MAGIC || in.readUnsignedByte() != VERSION) {
                throw new IOException("not a preferences token");
            }
            String user = readString(in);
            String theme = readString(in);
            int fontSize = in.readInt();
            int fileCount = readCount(in);
            List<String> recentFiles = new ArrayList<>(Math.min(fileCount, 1024));
            for (int i = 0; i < fileCount; i++) {
                recentFiles.add(readString(in));
            }
            int shortcutCount = readCount(in);
            Map<String, String> shortcuts = new LinkedHashMap<>();
            for (int i = 0; i < shortcutCount; i++) {
                String key = readString(in);
                shortcuts.put(key, readString(in));
            }
            if (in.read() != -1) {
                throw new IOException("trailing data in preferences token");
            }
            return new UserPrefs(user, theme, fontSize, recentFiles, shortcuts);
        } catch (EOFException e) {
            throw new IOException("truncated preferences token", e);
        }
    }

    private static void writeString(DataOutputStream out, String s) throws IOException {
        if (s == null) {
            out.writeInt(-1);
            return;
        }
        byte[] utf8 = s.getBytes(StandardCharsets.UTF_8);
        out.writeInt(utf8.length);
        out.write(utf8);
    }

    private static String readString(DataInputStream in) throws IOException {
        int length = in.readInt();
        if (length == -1) {
            return null;
        }
        if (length < 0 || length > in.available()) {
            throw new IOException("invalid string length in preferences token");
        }
        byte[] utf8 = new byte[length];
        in.readFully(utf8);
        return new String(utf8, StandardCharsets.UTF_8);
    }

    private static int readCount(DataInputStream in) throws IOException {
        int count = in.readInt();
        if (count < 0 || count > MAX_ENTRIES) {
            throw new IOException("invalid entry count in preferences token");
        }
        return count;
    }
}
