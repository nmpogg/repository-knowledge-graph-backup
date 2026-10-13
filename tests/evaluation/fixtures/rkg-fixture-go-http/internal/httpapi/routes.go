package httpapi

import (
	"github.com/gin-gonic/gin"
	"github.com/go-chi/chi"
	"github.com/gorilla/mux"
)

const OrdersPath = "/orders"

const suppressedPath = "RKG_TEST_SECRET_DO_NOT_PERSIST"

func GinHealth() {}

func ChiCatalog() {}

func MuxShipment() {}

func Register() {
	engine := gin.Default()
	engine.GET("/health", GinHealth)
	engine.GET(suppressedPath, GinHealth)

	suffix := "x"
	engine.POST("/dyn/"+suffix, GinHealth)

	chiRouter := chi.NewRouter()
	chiRouter.Get(OrdersPath, ChiCatalog)

	muxRouter := mux.NewRouter()
	muxRouter.HandleFunc("/shipments", MuxShipment).Methods("POST")
}
