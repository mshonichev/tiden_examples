package perftest

import io.gatling.core.Predef._
import io.gatling.http.Predef._
import io.gatling.http.protocol.HttpProtocolBuilder

import scala.concurrent.duration._

class HttpLoadScenario extends Simulation {

  val base_url = System.getProperty("base_url", "https://google.com/")
  var duration = Integer.getInteger("duration", 60)
  var load_factor = Integer.getInteger("load_factor", 1)
  var load_throttle = Integer.getInteger("load_throttle", 10)
  var page_name = System.getProperty("page_name", "Root page")

  val httpProtocol: HttpProtocolBuilder = http
    .baseUrl(base_url)
    .inferHtmlResources()
    .acceptHeader("*/*")
    .acceptEncodingHeader("gzip, deflate")
    .acceptLanguageHeader("en-US,en;q=0.5")
    .silentResources
    .disableFollowRedirect
    .asyncNameResolution("8.8.8.8")
    .disableCaching
    .disableFollowRedirect
    .check(status is 200)

  object BasicLoad {
    val start =
      exec(http(page_name)
        .get("")
      )
  }

  val basicLoad = scenario("Http load scenario")
    .forever(
       pace(load_throttle seconds)
         .exec(BasicLoad.start)
    )

  setUp(
    basicLoad
      .inject(
        rampUsers(load_factor)
          .during(duration seconds)
      )
      .protocols(httpProtocol)
  )
    .maxDuration((duration + 5) seconds)
}

