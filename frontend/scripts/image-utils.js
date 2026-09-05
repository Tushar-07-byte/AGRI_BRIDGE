// =========================================
// AGRIBRIDGE IMAGE URLS
// =========================================

const AGRIBRIDGE_API_BASE_URL =
    "http://127.0.0.1:8000";


/**
 * Resolves a listing photo_path to the FastAPI /uploads/ static mount.
 * Listings may contain either "uploads/file.jpg" or just "file.jpg".
 */
function getImageUrl(photoPath) {

    if (
        photoPath === null ||
        photoPath === undefined ||
        String(photoPath).trim() === ""
    ) {
        return "";
    }

    const normalizedPath =
        String(photoPath)
            .trim()
            .replace(/\\/g, "/")
            .replace(/^\/+/, "")
            .replace(/^uploads\/+/i, "");

    if (!normalizedPath) {
        return "";
    }

    const encodedPath =
        normalizedPath
            .split("/")
            .filter(Boolean)
            .map(segment =>
                encodeURIComponent(segment)
                    .replace(/\(/g, "%28")
                    .replace(/\)/g, "%29")
            )
            .join("/");

    return `${AGRIBRIDGE_API_BASE_URL}/uploads/${encodedPath}`;
}
