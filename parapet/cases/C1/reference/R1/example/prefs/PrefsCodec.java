package example.prefs;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.ObjectInputFilter;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.io.Serializable;
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

    private PrefsCodec() {
    }

    /**
     * Allowlist for preference tokens (JEP 290 serialization filter): only the
     * classes encode() writes may be deserialized, plus the array component
     * types that ArrayList and HashMap check while reading; every other class
     * is rejected before it is instantiated. Graph limits bound resource use.
     */
    private static final ObjectInputFilter PREFS_FILTER = ObjectInputFilter.Config.createFilter(
            "maxdepth=10;maxrefs=100000;maxbytes=4194304;maxarray=100000;"
            + "example.prefs.PrefsCodec$UserPrefs;"
            + "java.util.ArrayList;java.util.LinkedHashMap;java.util.HashMap;"
            + "java.lang.Object;java.util.Map$Entry;"
            + "!*");

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
        try (ObjectOutputStream out = new ObjectOutputStream(bytes)) {
            out.writeObject(prefs);
        }
        return Base64.getEncoder().encodeToString(bytes.toByteArray());
    }

    /** Restores preferences from a token produced by {@link #encode(UserPrefs)}. */
    public static UserPrefs decode(String token) throws IOException {
        byte[] data = Base64.getDecoder().decode(token);
        try (ObjectInputStream in = new ObjectInputStream(new ByteArrayInputStream(data))) {
            in.setObjectInputFilter(PREFS_FILTER);
            return (UserPrefs) in.readObject();
        } catch (ClassNotFoundException e) {
            throw new IOException("unknown class in preferences token", e);
        }
    }
}
