import graphene
from graphql_extensions.auth.decorators import staff_member_required

from ....graphql.product.types import Category
from ....graphql.utils import get_node
from ....product import models
from ...category.forms import CategoryForm
from ..mutations import (
    BaseMutation, ModelDeleteMutation, ModelFormMutation,
    ModelFormUpdateMutation, StaffMemberRequiredMutation)


class CategoryCreateMutation(StaffMemberRequiredMutation, ModelFormMutation):
    class Arguments:
        parent_id = graphene.ID()

    class Meta:
        form_class = CategoryForm

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        parent_id = input.pop('parent_id', None)
        kwargs = super().get_form_kwargs(root, info, **input)
        if parent_id:
            parent = get_node(info, parent_id, only_type=Category)
        else:
            parent = None
        kwargs['parent_pk'] = parent.pk if parent else None
        return kwargs


class CategoryUpdateMutation(
        StaffMemberRequiredMutation, ModelFormUpdateMutation):
    class Meta:
        form_class = CategoryForm

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        kwargs = super().get_form_kwargs(root, info, **input)
        kwargs['parent_pk'] = kwargs['instance'].parent_id
        return kwargs


class CategoryDelete(StaffMemberRequiredMutation, ModelDeleteMutation):
    class Meta:
        model = models.Category
