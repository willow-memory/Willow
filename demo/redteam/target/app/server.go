package main
import ("os/exec"; "crypto/tls"; "net/http")
func h(r *http.Request) {
    exec.Command("sh", "-c", r.URL.Query().Get("x"))
    c := &http.Client{Transport: &http.Transport{TLSClientConfig: &tls.Config{InsecureSkipVerify: true}}}
    _ = c
}
