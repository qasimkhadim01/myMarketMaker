func GetApiSignature(secret, channel string, requestParam []byte, ts int64) string {
	hash := hmac.New(sha512.New, []byte(secret))
	key := fmt.Sprintf("%s\n%s\n%s\n%d", "api", channel, string(requestParam), ts)
	hash.Write([]byte(key))
	return hex.EncodeToString(hash.Sum(nil))
}

func main() {

	// 1. login
	apiKey := "xxxxx"
	secret := "xxxxx"
	requestParam := ""
	channel := "spot.login"
	ts := time.Now().Unix()
	requestId := fmt.Sprintf("%d-%d", time.Now().UnixMilli(), 1)

	req := ApiRequest{
		Time:    ts,
		Channel: "spot.login",
		Event:   "api",
		Payload: ApiPayload{
			ApiKey:       apiKey,
			Signature:    GetApiSignature(secret, channel, []byte(requestParam), ts),
			Timestamp:    strconv.FormatInt(ts, 10),
			RequestId:    requestId,
			RequestParam: []byte(requestParam),
		},
	}

	fmt.Println(GetApiSignature(secret, channel, []byte(requestParam), ts))
	marshal, _ := json.Marshal(req)
	fmt.Println(string(marshal))

	// connect the ws
	u := url.URL{Scheme: "ws", Host: "xx.xx.xxx.xx:xxx", Path: "xxx"}
	websocket.DefaultDialer.TLSClientConfig = &tls.Config{RootCAs: nil, InsecureSkipVerify: true}
	c, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	if err != nil {
		panic(err)
	}
	c.SetPingHandler(nil)

	// read msg
	go func() {
		for {
			_, message, err := c.ReadMessage()
			if err != nil {
				c.Close()
				panic(err)
			}
			fmt.Printf("recv: %s\n", message)
		}
	}()

	err = c.WriteMessage(websocket.TextMessage, marshal)

	//ws create an order
	orderParam := orderParam{
		Text:         "t-123456",
		CurrencyPair: "ETH_BTC",
		Type:         "limit",
		Account:      "spot",
		Side:         "buy",
		Iceberg:      "0",
		Amount:       "1",
		Price:        "5.00032",
		TimeInForce:  "gtc",
		AutoBorrow:   false,
		StpAct:       "cn",
	}
	orderParamBytes, _ := json.Marshal(orderParam)

	//warn: if you want create batch_orders, the `RequestParam` : []byte([{orderParam},{orderParam},...])
	order_place := ApiRequest{
		Time:    ts,
		Channel: "spot.order_place",
		Event:   "api",
		Payload: ApiPayload{
			RequestId:    requestId,
			RequestParam: []byte(orderParamBytes),
		},
	}
	orderReqByte, _ := json.Marshal(order_place)
	err = c.WriteMessage(websocket.TextMessage, orderReqByte)

	if err != nil {
		panic(err)
	}

	select {}
}

type ApiRequest struct {
	App     string     `json:"app,omitempty"`
	Time    int64      `json:"time"`
	Id      *int64     `json:"id,omitempty"`
	Channel string     `json:"channel"`
	Event   string     `json:"event"`
	Payload ApiPayload `json:"payload"`
}
type ApiPayload struct {
	ApiKey       string          `json:"api_key,omitempty"`
	Signature    string          `json:"signature,omitempty"`
	Timestamp    string          `json:"timestamp,omitempty"`
	RequestId    string          `json:"req_id,omitempty"`
	RequestParam json.RawMessage `json:"req_param,omitempty"`
}

type OrderParam struct {
	Text         string `json:"text,omitempty"`
	CurrencyPair string `json:"currency_pair,omitempty"`
	Type         string `json:"type,omitempty"`
	Account      string `json:"account,omitempty"`
	Side         string `json:"side,omitempty"`
	Iceberg      string `json:"iceberg,omitempty"`
	Amount       string `json:"amount,omitempty"`
	Price        string `json:"price,omitempty"`
	TimeInForce  string `json:"time_in_force,omitempty"`
	AutoBorrow   bool   `json:"auto_borrow,omitempty"`
	StpAct       string `json:"stp_act,omitempty"`
}





package main

import (
	"crypto/hmac"
	"crypto/sha512"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"strconv"
	"time"
)

func GetApiSignature(secret, channel string, requestParam []byte, ts int64) string {
	hash := hmac.New(sha512.New, []byte(secret))
	key := fmt.Sprintf("%s\n%s\n%s\n%d", "api", channel, string(requestParam), ts)
	hash.Write([]byte(key))
	return hex.EncodeToString(hash.Sum(nil))
}

// example WebSocket signature calculation implementation in go
func main() {
	apiKey := "YOUR_API_KEY"
	secret := "YOUR_API_SECRET"
	requestParam := ""
	channel := "spot.login"
	ts := time.Now().Unix()
	requestId := fmt.Sprintf("%d-%d", time.Now().UnixMilli(), 1)

	req := ApiRequest{
		Time:    ts,
		Channel: "",
		Event:   "api",
		Payload: ApiPayload{
			ApiKey:       apiKey,
			Signature:    GetApiSignature(secret, channel, []byte(requestParam), ts),
			Timestamp:    strconv.FormatInt(ts, 10),
			RequestId:    requestId,
			RequestParam: []byte(requestParam),
		},
	}

	fmt.Println(GetApiSignature(secret, channel, []byte(requestParam), 1677813908) ==
		"2a8d9735bc0fa5cc7db97841482f317b515663d2a666abe8518ab214efada11b3da77ddc1e5fde529d5f780efa3366e302f5e3d2f7670460ae115801442e7461")

	marshal, _ := json.Marshal(req)
	fmt.Println(string(marshal))

	// connect ws service
	u := url.URL{Scheme: "ws", Host: "xxxx", Path: "xxxx"}
	websocket.DefaultDialer.TLSClientConfig = &tls.Config{RootCAs: nil, InsecureSkipVerify: true}
	c, _, err := websocket.DefaultDialer.Dial(u.String(), nil)
	if err != nil {
		panic(err)
	}
	c.SetPingHandler(nil)

	// read msg
	go func() {
		for {
			_, message, err := c.ReadMessage()
			if err != nil {
				c.Close()
				panic(err)
			}
			fmt.Printf("recv: %s\n", message)
		}
	}()

	err = c.WriteMessage(websocket.TextMessage, marshal)
	if err != nil {
		panic(err)
	}

	select {}
}

type ApiRequest struct {
	App     string     `json:"app,omitempty"`
	Time    int64      `json:"time"`
	Id      *int64     `json:"id,omitempty"`
	Channel string     `json:"channel"`
	Event   string     `json:"event"`
	Payload ApiPayload `json:"payload"`
}
type ApiPayload struct {
	ApiKey       string          `json:"api_key,omitempty"`
	Signature    string          `json:"signature,omitempty"`
	Timestamp    string          `json:"timestamp,omitempty"`
	RequestId    string          `json:"req_id,omitempty"`
	RequestParam json.RawMessage `json:"req_param,omitempty"`
}

Request example

{
  "time": 1681984544,
  "channel": "spot.login",
  "event": "api",
  "payload": {
    "api_key": "ea83fad2604399da16bf97e6eea772a6",
    "signature": "6fa3824c8141f2b2283108558ec50966d7caf749bf04a3b604652325b50b47d2343d569d848373d58e65c49d9622ba2e73dc25797abef11c9f20c07da741591e",
    "timestamp": "1681984544",
    "req_id": "request-1"
  }

