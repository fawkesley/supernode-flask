# supernode-flask

## Ubuntu 18.04 dependencies

`sudo apt install python3-pip`
`sudo pip3 install pipenv`

## Development

### Migrate the database

```
make migrate
```

This will create `database.sqlite3`


### Fake invoices

Set `FAKE_INVOICES=1` to prevent flask from talking to `lnd`. See `Makefile`.

## Invoice API

### Get an invoice (payment request) for a given product

```
$ curl -X POST http://localhost:5000/apiv1/shop/make-invoice -H 'content-type: application/json' -d '{"product": "web-haiku"}'
{
 "payment_request": "FAKE_c1be386d-fc63-4aa6-845d-fb4c0c77635f",
 "satoshis": 125000
}
```

## Check if an invoice (payment request) has been paid

Use the `payment_request` to check the status of the invoice:

```
$ curl http://localhost:5000/apiv1/shop/invoice/FAKE_c1be386d-fc63-4aa6-845d-fb4c0c77635f
{
  "paid": false,
  "payment_request": "FAKE_127c07ec-fd58-4b91-bcf0-bc7bb8c00180"
}
```
