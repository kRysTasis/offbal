from rest_framework import serializers
from .models import (
    mUser,
    Week,
    mSetting,
    Project,
    mUserProjectRelation,
    ProjectMemberShip,
    Section,
    Task,
    SubTask,
    Label,
    Karma,
)

import logging
import pytz
from datetime import (
    timezone,
    datetime,
    timedelta
)
from django.db.models import Q

from .utils import (
    utc_to_jst,
)

logging.basicConfig(
    level = logging.DEBUG,
    format = '''%(levelname)s %(asctime)s %(pathname)s:%(funcName)s:%(lineno)s
    %(message)s''')

logger = logging.getLogger(__name__)


class DynamicFieldsModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):

        fields = kwargs.pop('fields', None)

        # auth0_idを設定
        if 'context' in kwargs:
            self.auth0_id = kwargs['context']['view'].get_auth0_id()
        else:
            self.auth0_id = None

        super(DynamicFieldsModelSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

class UserSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = mUser
        fields = [
            'auth0_id',
            'auth0_name',
#             'email',
            'address',
        ]

    def create(self, validated_data):
        return mUser.objects.create(auth0_id=validated_data['auth0_id'], auth0_name=validated_data['auth0_name'])

class SettingSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = mSetting
        fields = [
            'target_user',
            'language',
            'time_zone',
            'weekly_beginning',
            'next_week_interpretation',
            'weekend_interpretation',
            'theme',
            'daily_task_number',
            'holiday',
            'karma',
            'vacation_mode',
        ]

class ProjectSerializer(DynamicFieldsModelSerializer):

    auth0_id = serializers.CharField(write_only=True)
    creator = serializers.CharField(read_only=True)
    tasks = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    favorite = serializers.SerializerMethodField()
    archived = serializers.SerializerMethodField()
    is_favorite = serializers.BooleanField(write_only=True, required=False)
    is_archived = serializers.BooleanField(write_only=True, required=False)

    isProject = serializers.BooleanField(read_only=True, default=True)

    class Meta:
        model = Project
        fields = [
            'id',
            'creator',
            'member',
            'name',
            'color',
            'favorite',
            'comment',
            'is_comp_public',
            'deleted',
            'archived',
            'auth0_id',
            'tasks',
            'sections',
            'is_favorite',
            'is_archived',
            'isProject',
        ]
    

    def get_favorite(self, obj):
        return obj.favorite.filter(auth0_id=self.auth0_id).exists()

    def get_archived(self, obj):
        return obj.archived.filter(auth0_id=self.auth0_id).exists()

    def get_tasks(self, obj):
        return TaskSerializer(obj.task_target_project.all(), many=True).data

    def get_sections(self, obj):
        return SectionSerializer(obj.section_target_project.all(), many=True).data

    def create(self, validated_data):
        try:
            user = mUser.objects.get(auth0_id=validated_data['auth0_id'])
        except mUser.DoesNotExist:
            logger.info('mUserが見つかりませんでした。')
            return None

        project = Project.objects.create(
                creator=user,
                name = validated_data['name'],
                color = validated_data['color'],
                # favorite = validated_data['is_favorite']
            )

        if validated_data['is_favorite']:
            project.favorite.add(user)
        return project

    def update(self, instance, validated_data):
        try:
            user = mUser.objects.get(auth0_id=validated_data['auth0_id'])
        except mUser.DoesNotExist:
            logger.info('mUserが見つかりませんでした。')
            return None

        instance.name = validated_data['name']
        instance.color = validated_data['color']

        if 'is_favorite' in validated_data:
            if validated_data['is_favorite']:
                instance.favorite.add(user)
            else:
                instance.favorite.remove(user)

        if 'is_archived' in validated_data:
            if validated_data['is_archived']:
                instance.archived.add(user)
            else:
                instance.archived.remove(user)

        instance.save()
        return instance

class ProjectMemberShipSerializer(DynamicFieldsModelSerializer):

    class Meta:
        model = ProjectMemberShip
        fields = [
            'invitee_user',
            'invited_user',
            'target_project',
            'accepted',
        ]

class SectionSerializer(DynamicFieldsModelSerializer):

    tasks = serializers.SerializerMethodField()
    target_project_name = serializers.CharField(read_only=True, source='target_project.name')

    isProject = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Section
        fields = [
            'id',
            'target_project',
            'name',
            'deleted',
            'archived',
            'tasks',
            'isProject',
            'target_project_name',
        ]

    def get_tasks(self, obj):
        return TaskSerializer(obj.task_target_section.all(), many=True).data

    def create(self, validated_data):
        section = Section.objects.create(
                target_project = validated_data['target_project'],
                name = validated_data['name'],
            )
        return section

class TaskSerializer(DynamicFieldsModelSerializer):

    auth0_id = serializers.CharField(write_only=True)
    project_name = serializers.CharField(write_only=True)
    deadline_str = serializers.CharField(write_only=True, allow_blank=True)
    remind_str = serializers.CharField(write_only=True, allow_blank=True)
    label_list = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        write_only=True,
    )
    section_name = serializers.CharField(write_only=True, allow_blank=True)

    target_user = serializers.CharField(read_only=True)
    target_project = serializers.CharField(read_only=True)
    label = serializers.SerializerMethodField(read_only=True)
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    sub_tasks = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id',
            'target_user',
            'target_project',
            'target_section',
            'content',
            'label',
            'priority',
            'deadline',
            'remind',
            'comment',
            'completed',
            'deleted',
            'is_comp_sub_public',
            'auth0_id',
            'project_name',
            'deadline_str',
            'remind_str',
            'label_list',
            'section_name',
            'created_at',
            'updated_at',
            'sub_tasks',
        ]

    def get_label(self, obj):
        return LabelSerializer(obj.label.all(), many=True).data

    def get_created_at(self, obj):
        return utc_to_jst(obj.created_at)

    def get_updated_at(self, obj):
        return utc_to_jst(obj.updated_at)

    def get_sub_tasks(self, obj):
        # とりあえず置いておく
        return None

    def create(self, validated_data):

        logger.debug('============TASKを作る================')
        logger.debug(validated_data)

        try:
            user = mUser.objects.get(auth0_id=validated_data['auth0_id'])
            project = Project.objects.get(name=validated_data['project_name'], creator=user)

            section_name = validated_data['section_name']
            section = Section.objects.get(name=section_name) if section_name != '' else None

        except mUser.DoesNotExist:
            logger.error('mUserが見つかりませんでした。')
            return None
        except Project.DoesNotExist:
            logger.error('Projectが見つかりませんでした。')
            return None
        except Section.DoesNotExist:
            logger.error('Sectionが見つかりませんでした。')
            return None

        dl_str = validated_data['deadline_str']
        rm_str = validated_data['remind_str']

        deadline = datetime.strptime(dl_str, '%Y-%m-%d %H:%M:%S') if dl_str != '' else None
        remind = datetime.strptime(rm_str, '%Y-%m-%d %H:%M:%S') if rm_str != '' else None

        task = Task.objects.create(
            content=validated_data['content'],
            comment=validated_data['comment'],
            target_user=user,
            target_project=project,
            target_section=section,
            priority=validated_data['priority'],
            deadline=deadline,
            remind=remind,
        )

        for label_name in validated_data['label_list']:
            try:
                label = Label.objects.get(name=label_name)
                task.label.add(label)
            except Label.DoesNotExist:
                logger.error('Labelが見つかりませんでした。')
                return None

        return task


class LabelSerializer(DynamicFieldsModelSerializer):

    auth0_id = serializers.CharField(write_only=True)
    author = serializers.CharField(read_only=True)
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = Label
        fields = [
            'id',
            'name',
            'author',
            'auth0_id',
            'created_at',
            'updated_at',
        ]

    def get_created_at(self, obj):
        return utc_to_jst(obj.created_at)

    def get_updated_at(self, obj):
        return utc_to_jst(obj.updated_at)


    def create(self, validated_data):

        try:
            user = mUser.objects.get(auth0_id=validated_data['auth0_id'])
        except mUser.DoesNotExist:
            logger.info('mUserが見つかりませんでした')
            return None

        label = Label.objects.create(
            name=validated_data['name'],
            author=user
        )

        return label


class KarmaSerializer(DynamicFieldsModelSerializer):

    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

    class Meta:
        model = Karma
        fields = [
            'target_user',
            'activity',
            'point',
            'created_at',
            'updated_at',
        ]

    def get_created_at(self, obj):
        return utc_to_jst(obj.created_at)

    def get_updated_at(self, obj):
        return utc_to_jst(obj.updated_at)
