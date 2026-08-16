// The sub-path this deployment is mounted under, e.g. "/varasto" (empty at the
// domain root). Django puts it on #root as a data attribute -- see
// templates/spa.html and kava_varasto.views.spa.
//
// A data attribute rather than a window global on purpose: the global needed an
// inline <script> in the shell, and hashing that for a Content-Security-Policy
// would tie the policy to one mount point, since the hash covers the
// interpolated value. Reading it from the DOM keeps `script-src 'self'` valid
// everywhere the app is mounted.
//
// The module scripts that import this are deferred, so #root is parsed by the
// time this runs.
const root = typeof document !== "undefined" ? document.getElementById("root") : null;

const scriptName = root?.dataset.scriptName || "";

export default scriptName;
