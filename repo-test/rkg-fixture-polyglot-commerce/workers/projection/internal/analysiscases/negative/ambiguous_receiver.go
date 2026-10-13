package negative

type ambiguousWorker interface {
	Work() string
}

type firstWorker struct{}
type secondWorker struct{}

func (firstWorker) Work() string  { return "first" }
func (secondWorker) Work() string { return "second" }

func InvokeAmbiguous(worker ambiguousWorker) string {
	return worker.Work()
}
