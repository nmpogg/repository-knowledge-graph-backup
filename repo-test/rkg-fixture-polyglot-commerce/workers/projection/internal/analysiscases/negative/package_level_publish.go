package negative

// PackageLevelResult is initialized at package scope; the call is not owned by a function handler.
var PackageLevelResult = localPublish()

func localPublish() string { return "not-a-message" }
