from cloudly.http.v2.api import HttpApi, Request, JsonResponse


class CreateModelApi(HttpApi):
    model = None
    schema = None

    def post(self, request: Request):
        data = request.json()
        if self.schema:
            request_schema = self.schema(**data, request=request)
            if not request_schema.is_valid():
                return JsonResponse({"error": str(request_schema.error)}, 400)
            data = request_schema.cleaned_data
        instance = self.create_instance(request, data)
        return JsonResponse(instance.to_dict(), 201)

    def create_instance(self, request: Request, data: dict):
        return self.model.items.create(**data)


class ListModelApi(HttpApi):
    model = None
    index_name = None

    def get(self, request: Request, id: str = None):
        if id:
            return self._get_one(request, id)
        return self._get_many(request)

    def _get_one(self, request: Request, id: str):
        instance = self.get_instance(request, id)
        if not instance:
            return JsonResponse({"error": "Not found"}, 404)
        return JsonResponse(instance.to_dict())

    def _get_many(self, request: Request):
        instances = self.list(request)
        return JsonResponse(
            {
                "data": [i.to_dict() for i in instances],
                "nextToken": instances.last_evaluated_key,
            }
        )

    def get_instance(self, request: Request, id: str):
        return self.model.items.get(id=id)

    def list(self, request: Request):
        limit = request.query.get("limit")
        next = request.query.get("next")
        instances = self.model.items.all(
            limit=limit,
            last_evaluated_key=next,
            index_name=self.index_name,
        )
        return instances


class UpdateModelApi(HttpApi):
    model = None
    schema = None

    def put(self, request: Request, id: str):
        data = request.json()
        if self.schema:
            request_schema = self.schema(**data, request=request)
            if not request_schema.is_valid():
                return JsonResponse({"error": str(request_schema.error)}, 400)
            data = request_schema.cleaned_data
        instance = self.update_instance(request, id, data)
        return JsonResponse(instance.to_dict())

    def update_instance(self, request: Request, id: str, data: dict):
        self.model.items.update(id, **data)
        return self.model.items.get(id=id)

    def patch(self, request: Request, id: str):
        return self.put(request, id)


class DeleteModelApi(HttpApi):
    model = None

    def delete(self, request: Request, id: str):
        self.delete_instance(request, id)
        return JsonResponse("", 204)

    def delete_instance(self, request: Request, id: str):
        return self.model.items.delete(id=id)
