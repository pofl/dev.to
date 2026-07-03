---
{
  "devto_id": null,
  "title": "Your title",
  "published": false,
  "description": "",
  "tags": "",
  "canonical_url": null,
  "main_image": null,
  "series": null,
  "organization_id": null
}
---

Software Engineering is not about applying the best architectural pattern. It's
about tradeoffs. It took me some time to learn this lesson. In this article I'd
like to discuss one instinct, where my intuition changed.

At work I write and maintain microservices. I have a particular approach to how
I structure those. Which seems to differ from the way how many colleagues,
interview candidates as well as people on the internet prefer to write
microservices.

## My approach

### Logic

"My" microservices usually have two layers.

- An API layer which includes each endpoint's business logic.
- A thin persistence layer encapsulating DB queries.
  - This persist layer is nothing like a proper Repository pattern.
  - What I want is DB queries wrapped in a method with a descriptive name and
    params and result mapped to proper types.
  - Since I've come to like sqlc the queries just naturally end up as a member
    of one "DB" instance but that is not important. In that sense you might not
    even call the persistence layer a layer since those "methods encapsulating
    queries" could be helpers that live anywhere.

The persistence layer here is not represented by an interface. It's just a class
/ Go struct encapsulating the DB interactions.

### Tests

Neither layer is tested in isolation. There are only blackbox tests. Since test
taxonomy varies from company to company let me elaborate what my blackbox tests
look like.

- The microservice's database is never mocked, it runs in a container during
  test execution. All tests make real DB queries.
- 90% of tests are run against the service's API. The whole HTTP server stack is
  instantiated (in Go: the full HTTP router as an instance of `http.Handler`),
  including the middlewares that would run in the production scenario and actual
  requests are constructed (in Go: `httptest.NewRequest`) and fired
  (`http.Handler#ServeHTTP`) against it.
- Other dependencies like peer microservices or third party dependencies are
  mocked.
- Things like Kafka/NATS and Temporal are mocked / not mocked on a case-by-case
  basis.
- Object storage is something that by intuition I would prefer to run as a real
  instance in a container, but in my most recent project it is abstracted and
  mocked and I haven't noticed any disadvantages to that.

## The common approach

What I perceive as the mainstream architecture is essentially a three-layered
separation of API, business logic, and persistence. This is essentially the
Clean Architecture / Onion-Architecture / Ports and Adapters.

Many people say that they test each of these layers in isolation, mocking or
faking the lower layers.

## Putting my advice in context

I have to reiterate that my proposed architecture is meant for microservices.
I.e. services that are maintained by one team only. I haven't deeply worked in a
monolith/modulith for a long time. There was one instance where a far-grown
microservice was opened up to a second team but in that instance my approach
worked well. The second team got their own module at the API layer and their own
persist layer.

I simple haven't seen my architecture put properly to test in a multi-team
context for me to claim it is always the better approach. In a monolith you will
most likely have one domain exposing an interface for other domains to use.

Heck even for a microservice there might come the day where I see benefits of
pivoting to the clean architecture. But I will default to the simple approach.

### On monoliths

If I have to expose my domain through an HTTP API and a code interface I would
probably have both in parallel and write tests for the interface level too. I
would probably have a shared helper object which allows reuse of business logic
between HTTP and interface. But I would probably not write tests for that shared
code and stick to black-box testing. I would also probably not ban business
logic from HTTP or interface in general.

### On Repositories

I tend to not find the Repository pattern worth it. Exceptions:

- You are following DDD, then stick to it if the use of Repositories is the
  convention in your org.
- You have reasons to believe you might switch databases in the future. In that
  scenario it could be worth it to strictly encapsulate DB operations in a clean
  interface. Otherwise the refactoring to achieve that interface after the fact
  is massive and painful.

My main doubt about repositories is transaction handling. From my observation
not even the DDD community appears to have an agreed-upon definition of whether
a Repository is a strictly object-oriented abstraction that treats transactions
as an implemtation-detail-to-be-hidden -- or if the repo merely encapsulates
queries which themselves don't know whether they are run in a Tx or not. And
then you also get into Unit Of Work territory which IME can be a pretty heavy
concept in terms of amount of code to maintain.

In my code transactions are handled outside the DB layer. Taking the KISS
mindset one step further, I even use the Tx to perform secondary side effects
like publishing a domain event, triggering a background job, mutating object
storage. The "right" way would be to make use of the Transactional Outbox
pattern in order to have transactional guarantees. But that again is a lot of
code to write, test and maintain.

What I do is start a Tx, perform DB mutations, trigger secondary side-effects
and only if they don't error do I commit the Tx. This only works as long as you
don't have to call multiple secondary systems. But if it is only the DB+1 then
it's good enough for me to assume that if I just ran some DB operations (i.e. I
know the DB is up) then I can safely assume that the DB is still up after
emitting one event to the queue.

## Thoughts on the common approach

What turns me off about the layer separation is the sheer amount of overhead and
busywork which that architecture creates.

### Congrats on the layers but they are still tightly coupled

Most of the methods in the business logic layer will be tailor-made for one
specific API endpoint. If you reduce the API layer to the most minimal amount of
IO serde and input validation and really put all business logic in the next
layer, you by definition will expose at least one tight-coupled method from the
logic layer per endpoint.

The point of separating modules is information hiding and reducing coupling. I'd
argue neither is achieved. On information hiding: A developer working on a
feature will almost always be aware of what all three layers do, so the
information hiding happens only on paper. As for coupling: Extend an endpoint
with a new input param or a new response field and you will quickly realize that
you will be touching all three layers.

### Complete isolation of layers is repetitive

If you take the idea of layer separation all the way you will create

- A type representing the serde targets of the API surface
- A type representing the params and result of DB operations
- A domain-model type used by the business-logic layer

At each layer you will have to convert and rearrange instances of the lower
layer type instance into the next layer.

For an extremely simple endpoint which runs one query and returns the result,
the conversion chore could be more code than the actual business logic.

### The testing overhead

Nothing stops you from having the layer separation and testing the service like
I do: on the API-level with running DB. This would be a sane decision IMO.

I can't wrap my head around why people would want to test each layer in
isolation. I get that some people strive for that "I see exactly where the bug
is based on which layer a test is red" but it's just not worth it IME. It's just
more tests to write and to maintain.

Also those unit-type tests just break all the time whenever you do refactoring.
Rename a method or change a parameter name? Tests break. If you only test by
sending requests and asserting responses, you can refactor anything you want and
tests will remain green.

The peak ill-advice is people implementing a parallel in-memory implementation
of their storage layer. Just run the DB during tests. It's fast enough, trust
me.
