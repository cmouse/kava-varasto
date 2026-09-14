// Mirrors kava_varasto.validators.PHONE_RE (the server-side source of
// truth: ^(\+358\d{6,12}|0\d{6,12})$). Used as an HTML <input pattern="...">
// value, which is implicitly anchored, so no ^/$ here.
const PHONE_PATTERN = "\\+358\\d{6,12}|0\\d{6,12}";

export default PHONE_PATTERN;
